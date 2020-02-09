from model import StyleTransferModel
from fast_neural_style.neural_style.neural_style import transfer
from telegram_token import token
import numpy as np
from PIL import Image
from io import BytesIO

# В бейзлайне пример того, как мы можем обрабатывать две картинки, пришедшие от пользователя.
# При реалиазации первого алгоритма это Вам не понадобится, так что можете убрать загрузку второй картинки.
# Если решите делать модель, переносящую любой стиль, то просто вернете код)

model = StyleTransferModel()
first_image_file = { }
info = {}

def send_prediction_on_photo(bot, update):
	# Нам нужно получить две картинки, чтобы произвести перенос стиля, но каждая картинка приходит в
	# отдельном апдейте, поэтому в простейшем случае мы будем сохранять id первой картинки в память,
	# чтобы, когда уже придет вторая, мы могли загрузить в память уже сами картинки и обработать их.
	chat_id = update.message.chat_id
	print("Got image from {}".format(chat_id))

	# получаем информацию о картинке
	image_info = update.message.photo[-1]
	image_file = bot.get_file(image_info)

	if chat_id in first_image_file:

		# первая картинка, которая к нам пришла станет content image, а вторая style image
		content_image_stream = BytesIO()
		first_image_file[chat_id].download(out=content_image_stream)
		del first_image_file[chat_id]

		style_image_stream = BytesIO()
		image_file.download(out=style_image_stream)

		# output = model.transfer_style(content_image_stream, style_image_stream)
		output = transfer(content_image_stream)

		# теперь отправим назад фото
		output_stream = BytesIO()
		output.save(output_stream, format='PNG')
		output_stream.seek(0)
		bot.send_photo(chat_id, photo=output_stream)
		print("Sent Photo to user")
	else:
		first_image_file[chat_id] = image_file


def cancel(context, update):
	user = update.message.from_user
	logger.info("User %s canceled the conversation.", user.first_name)
	update.message.reply_text('Bye! I hope we can talk again some day.',
							  reply_markup=ReplyKeyboardRemove())

	return ConversationHandler.END

def start(update, context):
	reply_keyboard = [['candy', 'mosaic', 'rain_princess', 'udnie']]

	context.bot.send_message(chat_id=update.effective_chat.id, text="'Hi! I will make an artwork you. Send /cancel to stop talking to me.\n\n Which style do you prefer?", reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True))
	return GENDER

def gender(update, context):
	user = update.message.from_user
	chat_id = update.message.chat_id
	info[chat_id] = [update.message.text, None]
	logger.info("Style of %s: %s", user.first_name, update.message.text)
	update.message.reply_text('Okay. Now you must send me a picture',reply_markup=ReplyKeyboardRemove())

	return PHOTO

def photo(update, bot):
	# user = update.message.from_user
	# photo_file = update.message.photo[-1].get_file()
	# photo_file.download('user_photo.jpg')
	# logger.info("Photo of %s: %s", user.first_name, 'user_photo.jpg')
	chat_id = update.message.chat_id
	update.message.reply_text('Got it! Wait and i will send you the result')

	print("Got image from {}".format(chat_id))

	# получаем информацию о картинке

	# image_info = update.message.photo[-1]
	# image_file = bot.get_file(image_info)
	image_file = update.message.photo[-1].get_file()

	first_image_file[chat_id] = image_file
	# if chat_id in first_image_file:

	# первая картинка, которая к нам пришла станет content image
	content_image_stream = BytesIO()
	first_image_file[chat_id].download(out=content_image_stream)
	info[chat_id][1] = content_image_stream
	del first_image_file[chat_id]

	output = transfer(info[chat_id][1], info[chat_id][0])

	# теперь отправим назад фото
	output_stream = BytesIO()
	output.save(output_stream, format='PNG')
	output_stream.seek(0)
	update.message.reply_text('Enjoy!')
	bot.send_photo(chat_id, photo=output_stream)
	print("Sent Photo to user")
	# else:
	# 	first_image_file[chat_id] = image_file

	return ConversationHandler.END


if __name__ == '__main__':
	from telegram import (ReplyKeyboardMarkup, ReplyKeyboardRemove)
	from telegram.ext import (Updater, CommandHandler, MessageHandler, Filters, RegexHandler,
						  ConversationHandler, Filters)
	import logging

	# Включим самый базовый логгинг, чтобы видеть сообщения об ошибках
	logging.basicConfig(
		format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
		level=logging.INFO)
	logger = logging.getLogger(__name__)
	GENDER, PHOTO, LOCATION, BIO = range(4)
	# используем прокси, так как без него у меня ничего не работало.
	# если есть проблемы с подключением, то попробуйте убрать прокси или сменить на другой
	# проекси ищется в гугле как "socks4 proxy"
	updater = Updater(token=token, use_context=True)
	#, request_kwargs={ 'proxy_url': 'socks4://136.243.48.56:1080' }
	# В реализации большого бота скорее всего будет удобнее использовать Conversation Handler
	# вместо назначения handler'ов таким способом
	# updater.dispatcher.add_handler(MessageHandler(Filters.photo, send_prediction_on_photo))

	conv_handler = ConversationHandler(
		entry_points=[CommandHandler('start', start)],

		states={
			# GENDER: [RegexHandler('^(Boy|Girl|Other)$', gender)],
			GENDER: [MessageHandler(Filters.text, gender)],

			PHOTO: [MessageHandler(Filters.photo, photo)]
		},

		fallbacks=[CommandHandler('cancel', cancel)]
	)
	updater.dispatcher.add_handler(conv_handler)

	updater.start_polling()
