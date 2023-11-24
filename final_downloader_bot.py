import asyncio
import logging
from aiogram import Bot, Dispatcher, F
from aiogram.types import Message, FSInputFile
from aiogram.utils.media_group import MediaGroupBuilder
from pytube import YouTube, Playlist
from aiogram.filters import BaseFilter
import re, os
from background import keep_alive

logging.basicConfig(
  # filename='app.log', 
  level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')


logger = logging.getLogger('bot_logger')


class LinkCheckFilter(BaseFilter):
    async def __call__(self, msg: Message) -> bool:
        if msg.text:
            return self.isValidURL(msg.text)

        # https://www.youtube.com/watch?v=4yJEV8aAtLE

    def isValidURL(self, link) -> bool:

        # Regex to check valid URL 
        regex = ("((http|https)://)(www.)?" +
                "[a-zA-Z0-9@:%._\\+~#?&//=]" +
                "{2,256}\\.[a-z]" +
                "{2,6}\\b([-a-zA-Z0-9@:%" +
                "._\\+~#?&//=]*)")

        # Compile the ReGex
        p = re.compile(regex)

        # If the string is empty 
        # return false
        if  link == None:
            return False

        # Return if the linking 
        # matched the ReGex
        if re.search(p, link):
            return True
        else:
            return False



bot = Bot(token=os.environ['TOKEN'])
dp = Dispatcher()

@dp.message(LinkCheckFilter())
async def download_yt(msg: Message):
    msg_edit = await msg.reply('Downloading...')

    loop = asyncio.get_event_loop()
    # Use loop.run_in_executor() to run the download_video function asynchronously

    if msg.text.find('playlist') > -1:
        isVideo, video_path = await download_playlist(msg.text, msg_edit)
        if isVideo:
          await send_multiple(video_path, msg)
          await loop.run_in_executor(None, clear_video, video_path)
          return
    else:
        isVideo, video_path = await loop.run_in_executor(None, download_video, msg.text)
        if isVideo:
            await msg.answer_audio(audio=FSInputFile(video_path))
            await loop.run_in_executor(None, clear_video, video_path)
            return

    await msg.answer('Sorry, could not download. Check the logger')


def clear_video(files: str | list):
# audio_directory = 'C:\\Users\\anara\\vscode\\teleBot\\audio\\'  #'/home/runner/Python/audio/' 
    if isinstance(files, str):
        if os.path.exists(files):
            os.remove(files)
            logger.info('audio is removed')
    else:
        for file in files:
            if os.path.exists(file):
                os.remove(file)
        logger.info('palylist is removed')
    
    

def download_video(url):    
    try:
        video = YouTube(url)
        stream = video.streams.filter(only_audio=True, file_extension='mp4').first()
        path_vid = stream.download( output_path='audio')#, filename=f"{video.title}.mp3")
        logger.info(f"The video is downloaded in MP4: {path_vid}")
        # print(f"The video is downloaded in MP3: {path_vid}")
        return True, path_vid
    except Exception as e:
        logger.warning("Unable to fetch video information. Please check the video URL or your network connection.")
        logger.exception(e)
        return False, None

async def download_playlist(url, msg: Message):
    try:
        p = Playlist(url)
        video_paths = []
        count = 0
        logger.info(f'Downloading: {p.title}')
        for video in p.videos:
            path_vid = video.streams.filter(only_audio=True, file_extension='mp4').first().download(output_path='audio')
            logger.info(f'Dowloaded: {path_vid}')
            video_paths.append(path_vid) 
            count+=1
            if not count % 5:
                await msg.edit_text(f'Downloaded audio: {count}/{len(p.videos)}')

        await msg.edit_text(f'Total audio: {count}/{len(p.videos)}')
        return True, video_paths
    except Exception as e:
        logger.warning("Unable to fetch playlist information. Please check the video URL or your network connection.")
        logger.exception(e)
        return False, None


async def send_multiple(video_path: list, msg: Message):
  curr_size = 0
  curr_len = 0
  max_size = 50*1024*1024
  media_group = MediaGroupBuilder()
  for video in video_path:
      curr_len+=1
      curr_size+= os.path.getsize(video)
      if curr_size <= max_size and curr_len <= 10:
          media_group.add_audio(FSInputFile(video))
          # print(f'curr_size: {curr_size}, curr_len: {curr_len}, video: {video}')
      else:
          await msg.answer_media_group(media=media_group.build())
          media_group = MediaGroupBuilder()
          curr_size = 1
          curr_len = 1
          media_group.add_audio(FSInputFile(video))
          # print(f'curr_size: {curr_size}, curr_len: {curr_size}, video: {video}')

  if curr_size > 0:
      # logger.info('inside curr_size > 0')
      await msg.answer_media_group(media=media_group.build())



@dp.message(F.text)
async def message_with_text(message: Message):
    await message.answer("Это текстовое сообщение! Send me a link to a video or a public playlist")
@dp.message(F.sticker)
async def message_with_sticker(message: Message):
    await message.answer("Это стикер!")
@dp.message(F.animation)
async def message_with_gif(message: Message):
    await message.answer("Это GIF!")
@dp.message(F.photo)
async def message_with_gif(message: Message):
    await message.answer("Это photo!")
@dp.message(F.audio)
async def message_with_gif(message: Message):
    await message.answer("Это audio!")
@dp.message(F.file) #doesnt work
async def message_with_gif(message: Message):
    await message.answer("Это file!")
@dp.message(F.video)
async def message_with_gif(message: Message):
    await message.answer("Это video!")




async def main():
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == "__main__":
    keep_alive()
    asyncio.run(main())


