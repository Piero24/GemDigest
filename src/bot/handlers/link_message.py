"""This module contains the implementation for handling messages that contain 
    URLs in a Telegram bot. It includes an asynchronous function to process 
    incoming messages, extract URLs, crawl them for content, and respond to 
    the user with generated text and links to articles. Has a separate function
    to handle messages that do not contain any URLs.

Functions:
    handle_link_message(message: Message, bot: AsyncTeleBot) -> None:
        Handles messages containing URLs by extracting and processing the links.
    handle_no_link_message(message: Message, bot: AsyncTeleBot) -> None:
        Handles messages that do not contain any URLs.
"""

from telebot.async_telebot import AsyncTeleBot
from telebot.types import Message

from crawler import crawl_urls, ScrapeResult
from gemini import GeminiAPIClient, GeminiResponse
from utils import link_utils

from ..bot_utils import message_markup
    

async def handle_link_message(message: Message, bot: AsyncTeleBot) -> None:
    """Handles messages containing URLs by extracting and processing the links.

    This asynchronous function performs the following tasks:
        1. Extracts URLs from the incoming text message.
        2. Crawls the extracted URLs to scrape their content and sub-links.
        3. Generates a text response based on the scraped content using 
            the Gemini API.
        4. Replies to the user with the generated text, including a button 
            linking to the original article.

    Args:
        message (Message): The incoming Telegram message containing the URLs.
        bot (AsyncTeleBot): The bot instance used to send the reply message.

    Returns:
        None: This function does not return a value.
    """

    # show GemDigest is typing on the chat top bar
    await bot.send_chat_action(message.chat.id, "typing")

    # TODO: add automatic addition of 'https://' to URLs without a scheme
    urls = link_utils.extract_urls(message.text)

    urls = filter(lambda x: not link_utils.is_youtube(x), urls)
            
    scrape_results: list[ScrapeResult] = await crawl_urls(urls)
    
    for result in scrape_results:
        prompt = result.content + "\n\n" + "\n".join(result.sub_urls)
        output: GeminiResponse = await GeminiAPIClient.generate_text(prompt)

        # TODO: add error_message formatting

        await bot.reply_to(
            message,
            output.text if output.text else output.error_message,
            disable_notification=True,
            parse_mode='html',
            reply_markup=message_markup.generate_article_button_markup(
                result.original_url
                )
        )


async def handle_no_link_message(message: Message, bot: AsyncTeleBot) -> None:
    """Handles messages that do not contain any URLs.

    This asynchronous function replies to the user with a message indicating 
    that no URLs were found in the incoming message.

    Args:
        message (Message): The incoming Telegram message without any URLs.
        bot (AsyncTeleBot): The bot instance used to send the reply message.

    Returns:
        None: This function does not return a value.
    """

    no_link_message = (
        "Oops\\! 🤖 It looks like there's no link in your message\\." 
        "📭 Drop a link and let me work my magic\\! ✨"
    )

    await bot.reply_to(
        message,
        no_link_message,
        parse_mode="markdownv2",
        disable_notification=True
    )