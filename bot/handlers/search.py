"""
Search command and conversation handlers.
"""

import logging

from telegram import Update
from telegram.ext import (
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
    ConversationHandler,
    MessageHandler,
    filters,
)

from ..api import api_client, downloader
from ..utils.keyboard import (
    ANIME_PREFIX,
    BACK_PREFIX,
    DUB_TOGGLE,
    EPISODE_PREFIX,
    NOOP,
    PAGE_PREFIX,
    QUALITY_PREFIX,
    build_anime_list_keyboard,
    build_episode_list_keyboard,
    build_quality_keyboard,
)
from ..utils.state import ConversationState, sessions

logger = logging.getLogger(__name__)


async def search_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Handle /search command.

    Usage:
        /search One Piece  -> Direct search
        /search           -> Prompts for query
    """
    user_id = update.effective_user.id
    sessions.reset_search(user_id)

    # Check if query provided with command
    if context.args:
        query = " ".join(context.args)
        return await perform_search(update, context, query)

    # Otherwise, ask for query
    await update.message.reply_text(
        "🔍 *Search Anime*\n\n" "Please enter the anime name you want to search for:",
        parse_mode="Markdown",
    )
    return ConversationState.WAITING_SEARCH_QUERY


async def receive_search_query(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> int:
    """Handle search query message."""
    query = update.message.text.strip()

    if not query:
        await update.message.reply_text("Please enter a valid search query.")
        return ConversationState.WAITING_SEARCH_QUERY

    return await perform_search(update, context, query)


async def perform_search(
    update: Update, context: ContextTypes.DEFAULT_TYPE, query: str
) -> int:
    """Execute search and display results."""
    user_id = update.effective_user.id
    session = sessions.get(user_id)

    # Show searching message
    message = await update.effective_message.reply_text(
        f"🔍 Searching for: *{query}*...",
        parse_mode="Markdown",
    )

    try:
        # Perform search
        results = await api_client.search(query, session.translation_type)

        if not results:
            await message.edit_text(
                f"❌ No results found for: *{query}*\n\n"
                "Try a different search term.",
                parse_mode="Markdown",
            )
            return ConversationHandler.END

        # Store results in session
        session.search_query = query
        session.search_results = results
        session.anime_page = 0

        # Build and send keyboard
        keyboard = build_anime_list_keyboard(
            results,
            page=0,
            translation_type=session.translation_type,
        )

        await message.edit_text(
            f"🎬 *Search Results for:* {query}\n"
            f"Found {len(results)} anime(s). Select one:",
            reply_markup=keyboard,
            parse_mode="Markdown",
        )

        return ConversationState.SELECTING_ANIME

    except Exception as e:
        logger.error(f"Search error: {e}")
        await message.edit_text(f"❌ Error during search: {str(e)}")
        return ConversationHandler.END


async def select_anime_callback(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> int:
    """Handle anime selection from inline keyboard."""
    query = update.callback_query
    await query.answer()

    user_id = update.effective_user.id
    session = sessions.get(user_id)
    data = query.data

    # Handle no-op
    if data == NOOP:
        return ConversationState.SELECTING_ANIME

    # Handle pagination
    if data.startswith(PAGE_PREFIX + "anime:"):
        page = int(data.split(":")[-1])
        session.anime_page = page

        keyboard = build_anime_list_keyboard(
            session.search_results,
            page=page,
            translation_type=session.translation_type,
        )
        await query.edit_message_reply_markup(reply_markup=keyboard)
        return ConversationState.SELECTING_ANIME

    # Handle dub/sub toggle
    if data == DUB_TOGGLE:
        session.translation_type = "dub" if session.translation_type == "sub" else "sub"

        # Re-search with new translation type
        try:
            results = await api_client.search(
                session.search_query, session.translation_type
            )
            session.search_results = results
            session.anime_page = 0

            keyboard = build_anime_list_keyboard(
                results,
                page=0,
                translation_type=session.translation_type,
            )

            mode_text = "DUB" if session.translation_type == "dub" else "SUB"
            await query.edit_message_text(
                f"🎬 *Search Results for:* {session.search_query} ({mode_text})\n"
                f"Found {len(results)} anime(s). Select one:",
                reply_markup=keyboard,
                parse_mode="Markdown",
            )
        except Exception as e:
            await query.edit_message_text(f"❌ Error: {e}")
            return ConversationHandler.END

        return ConversationState.SELECTING_ANIME

    # Handle cancel
    if data == f"{BACK_PREFIX}cancel":
        await query.edit_message_text("Search cancelled.")
        sessions.clear(user_id)
        return ConversationHandler.END

    # Handle anime selection
    if data.startswith(ANIME_PREFIX):
        anime_id = data[len(ANIME_PREFIX) :]

        # Find selected anime
        selected = next((a for a in session.search_results if a.id == anime_id), None)
        if not selected:
            await query.edit_message_text("❌ Anime not found. Please search again.")
            return ConversationHandler.END

        session.selected_anime_id = anime_id
        session.selected_anime_name = selected.name

        # Fetch episodes
        await query.edit_message_text(
            f"📺 Loading episodes for *{selected.name}*...",
            parse_mode="Markdown",
        )

        try:
            episodes = await api_client.get_episodes(anime_id, session.translation_type)

            if not episodes:
                await query.edit_message_text(
                    f"❌ No {session.translation_type.upper()} episodes available for *{selected.name}*",
                    parse_mode="Markdown",
                )
                return ConversationHandler.END

            session.episodes = episodes
            session.episode_page = 0

            keyboard = build_episode_list_keyboard(episodes, page=0)

            await query.edit_message_text(
                f"📺 *{selected.name}*\n"
                f"Type: {session.translation_type.upper()}\n"
                f"Episodes: {len(episodes)}\n\n"
                "Select an episode:",
                reply_markup=keyboard,
                parse_mode="Markdown",
            )

            return ConversationState.SELECTING_EPISODE

        except Exception as e:
            logger.error(f"Episodes fetch error: {e}")
            await query.edit_message_text(f"❌ Error loading episodes: {str(e)}")
            return ConversationHandler.END

    return ConversationState.SELECTING_ANIME


async def select_episode_callback(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> int:
    """Handle episode selection."""
    query = update.callback_query
    await query.answer()

    user_id = update.effective_user.id
    session = sessions.get(user_id)
    data = query.data

    # Handle no-op
    if data == NOOP:
        return ConversationState.SELECTING_EPISODE

    # Handle pagination
    if data.startswith(PAGE_PREFIX + "ep:"):
        page = int(data.split(":")[-1])
        session.episode_page = page

        keyboard = build_episode_list_keyboard(session.episodes, page=page)
        await query.edit_message_reply_markup(reply_markup=keyboard)
        return ConversationState.SELECTING_EPISODE

    # Handle back to search
    if data == f"{BACK_PREFIX}search":
        keyboard = build_anime_list_keyboard(
            session.search_results,
            page=session.anime_page,
            translation_type=session.translation_type,
        )
        await query.edit_message_text(
            f"🎬 *Search Results for:* {session.search_query}\n"
            f"Found {len(session.search_results)} anime(s). Select one:",
            reply_markup=keyboard,
            parse_mode="Markdown",
        )
        return ConversationState.SELECTING_ANIME

    # Handle episode selection
    if data.startswith(EPISODE_PREFIX):
        episode = data[len(EPISODE_PREFIX) :]
        session.selected_episode = episode

        await query.edit_message_text(
            f"⏳ Loading Episode {episode} of *{session.selected_anime_name}*...",
            parse_mode="Markdown",
        )

        try:
            # Get video streams directly
            video_streams = await api_client.get_video_streams(
                session.selected_anime_id,
                episode,
                session.translation_type,
            )

            if not video_streams:
                await query.edit_message_text(
                    f"❌ No video streams found for Episode {episode}.\n"
                    "The sources may be temporarily unavailable.",
                    parse_mode="Markdown",
                )
                keyboard = build_episode_list_keyboard(
                    session.episodes, page=session.episode_page
                )
                await query.edit_message_reply_markup(reply_markup=keyboard)
                return ConversationState.SELECTING_EPISODE

            session.video_streams = video_streams

            # If only one quality, send directly
            if len(video_streams) == 1:
                return await send_video(query, session, video_streams[0])

            # Otherwise, show quality selection
            keyboard = build_quality_keyboard(video_streams)

            await query.edit_message_text(
                f"🎬 *{session.selected_anime_name}* - Episode {episode}\n\n"
                "Select video quality:",
                reply_markup=keyboard,
                parse_mode="Markdown",
            )

            return ConversationState.SELECTING_QUALITY

        except Exception as e:
            logger.error(f"Episode loading error: {e}")
            await query.edit_message_text(f"❌ Error loading episode: {str(e)}")
            return ConversationState.SELECTING_EPISODE

    return ConversationState.SELECTING_EPISODE


async def select_quality_callback(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> int:
    """Handle quality selection."""
    query = update.callback_query
    await query.answer()

    user_id = update.effective_user.id
    session = sessions.get(user_id)
    data = query.data

    # Handle back to episodes
    if data == f"{BACK_PREFIX}episodes":
        keyboard = build_episode_list_keyboard(
            session.episodes, page=session.episode_page
        )
        await query.edit_message_text(
            f"📺 *{session.selected_anime_name}*\n"
            f"Type: {session.translation_type.upper()}\n"
            f"Episodes: {len(session.episodes)}\n\n"
            "Select an episode:",
            reply_markup=keyboard,
            parse_mode="Markdown",
        )
        return ConversationState.SELECTING_EPISODE

    # Handle quality selection
    if data.startswith(QUALITY_PREFIX):
        try:
            idx = int(data[len(QUALITY_PREFIX) :])
            if 0 <= idx < len(session.video_streams):
                stream = session.video_streams[idx]
                return await send_video(query, session, stream)
        except (ValueError, IndexError):
            pass

        # Fallback to first stream
        if session.video_streams:
            return await send_video(query, session, session.video_streams[0])

    return ConversationState.SELECTING_QUALITY


async def send_video(query, session, stream) -> int:
    """Send the video to user via Telegram."""
    # Edit message to show loading
    await query.edit_message_text(
        f"📤 Sending *{session.selected_anime_name}* - Episode {session.selected_episode}...\n"
        f"Quality: {stream.resolution}\n\n"
        "Please wait, this may take a moment...",
        parse_mode="Markdown",
    )

    try:
        # Try to send video by URL (Telegram fetches it)
        # This works for larger files than the 50MB upload limit
        from telegram import InputFile
        import os
        file_path = await downloader.download_video(stream)

        with open(file_path, 'rb') as video_file:
            await query.message.reply_video(
                video=InputFile(video_file, filename="video.mp4"),#stream.url,
                caption=(
                    f"🎬 *{session.selected_anime_name}*\n"
                    f"📺 Episode: {session.selected_episode}\n"
                    f"📊 Quality: {stream.resolution}\n"
                    # f"🎥 Provider: {stream.provider}"
                ),
                parse_mode="Markdown",
                supports_streaming=True,
            )

        # Delete the loading message
        await query.message.delete()

    except Exception as e:
        logger.warning(f"Video send failed: {e}, falling back to URL")

        # Fallback: send URL as text
        response = (
            f"🎬 *{session.selected_anime_name}*\n"
            f"📺 Episode: {session.selected_episode}\n"
            f"📊 Quality: {stream.resolution}\n"
            # f"🎥 Provider: {stream.provider}\n"
            # f"📁 Format: {stream.format.upper()}\n\n"
            f"🔗 *Stream URL:*\n`{stream.url}`"
        )

        # if stream.subtitle_url:
        #     response += f"\n\n📝 *Subtitles:*\n`{stream.subtitle_url}`"
        #     response += f"\n\n📝 *Subtitles:*\n"

        if stream.referrer:
            response += f"\n\n⚠️ *Note:* Some players may require this referer:\n`{stream.referrer}`"

        await query.edit_message_text(response, parse_mode="Markdown")

    return ConversationHandler.END


async def cancel_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle /cancel command."""
    user_id = update.effective_user.id
    sessions.clear(user_id)
    await update.message.reply_text("Search cancelled. Use /search to start again.")
    return ConversationHandler.END


def get_conversation_handler() -> ConversationHandler:
    """Create and return the search conversation handler."""
    return ConversationHandler(
        entry_points=[
            CommandHandler("search", search_command),
        ],
        states={
            ConversationState.WAITING_SEARCH_QUERY: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, receive_search_query),
            ],
            ConversationState.SELECTING_ANIME: [
                CallbackQueryHandler(select_anime_callback),
            ],
            ConversationState.SELECTING_EPISODE: [
                CallbackQueryHandler(select_episode_callback),
            ],
            ConversationState.SELECTING_QUALITY: [
                CallbackQueryHandler(select_quality_callback),
            ],
        },
        fallbacks=[
            CommandHandler("cancel", cancel_command),
            CommandHandler("search", search_command),  # Allow restarting search
        ],
        per_user=True,
        per_chat=True,
    )
