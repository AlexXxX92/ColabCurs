from io import BytesIO
import random
import requests
import vk_api
import time
from vk_api import VkUpload
from vk_api.longpoll import VkLongPoll, VkEventType
from vk_api.keyboard import VkKeyboard, VkKeyboardColor
from modelsdb.model import Favorits, VK_ID, VK_Favorit
import datetime
from datetime import datetime


class VK:
    def __init__(self, token, session, token_user):
        self.token = token
        self.session = session
        self.token_user = token_user
        vk_session = vk_api.VkApi(token=token)  # токен
        vk_session_user = vk_api.VkApi(token=token_user)
        self.vk = vk_session.get_api()
        self.vk_user = vk_session_user.get_api()
        self.longpoll = VkLongPoll(vk_session)


    def upload_photo(self, url):
        upload = VkUpload(self.vk)
        img = requests.get(url).content
        f = BytesIO(img)

        response = upload.photo_messages(f)[0]

        owner_id = response['owner_id']
        photo_id = response['id']
        access_key = response['access_key']

        return owner_id, photo_id, access_key

    def send_photo(self, id_vk, owner_id, photo_id, access_key):
        key = VkKeyboard()
        key.add_button('Добавить в избранное❤.', VkKeyboardColor.POSITIVE)
        key.add_button('Далее', VkKeyboardColor.SECONDARY)
        key.add_button('Стоп!', VkKeyboardColor.NEGATIVE)
        attachment = f'photo{owner_id}_{photo_id}_{access_key}'
        self.vk.messages.send(
            random_id=0,
            peer_id=id_vk,
            attachment=attachment,
            keyboard=key.get_keyboard()
        )

    def get_data(self,id_vk):
        date_now = datetime.now().date()
        date_only = datetime.strftime(date_now, '%Y')
        user_info_get = self.vk.users.get(user_ids=id_vk, fields='sex, city, bdate')
        # sex 0 не указан, 1 жен, 2 муж
        try:
            age = int(date_only) - int(user_info_get[0]['bdate'].split('.')[2])
        except KeyError:
            self.vk.messages.send(user_id=id_vk,
                                  message='У вас не указан возвраст. Сколько вам лет?',
                                  random_id=0)
            for event in self.longpoll.listen():
                if event.type == VkEventType.MESSAGE_NEW:
                    if event.to_me:
                        try:
                            msg = event.text.lower()
                            try:
                                age = int(msg)
                                break
                            except ValueError:
                                self.send_msg(id_vk, 'Неправильный ввод, попробуйте снова!')
                                continue
                        except:
                            self.send_msg(id_vk, 'Неправильный ввод, попробуйте снова!')
                            continue
        sex = user_info_get[0]['sex']
        city = user_info_get[0]['city']['title'] if 'city' in user_info_get[0] else ''  # Возвращет None, если не указан город
        if city == "":
            self.vk.messages.send(user_id=id_vk,
                                  message='У вас не указан город! В каком городе будем искать?',
                                  random_id=0)
            for event in self.longpoll.listen():
                if event.type == VkEventType.MESSAGE_NEW:
                    if event.to_me:
                        try:
                            city = event.text
                            break
                        except:
                            self.vk.messages.send(user_id=id_vk,
                                                  message='Неправильный ввод, попробуйте снова!',
                                                  random_id=0)
                            continue


        return {'age': age, 'sex': sex, 'city': city}


    def search_user(self, id_vk):
        data_user = self.get_data(id_vk)
        if data_user['sex'] == 1:
            sex = 2
        elif data_user['sex'] == 2:
            sex = 1
        else:
            sex = 0
        user_info_get = self.vk_user.users.search(sex=sex,
                                                  hometown=data_user['city'],
                                                  age_from=data_user['age'],
                                                  age_to=data_user['age']+5,
                                                  has_photo=1,
                                                )
        count = 1000 if user_info_get['count'] >= 1000 else user_info_get['count']
        for i in range(count):
            offset = i
            info = self.vk_user.users.search(sex=sex,
                                      hometown=data_user['city'],
                                      age_from=data_user['age'],
                                      age_to=data_user['age'] + 5,
                                      has_photo=1,
                                      offset=offset,
                                      )
            random.shuffle(info['items'])
            id_favorit =info['items'][0]['id']
            name = f'{info['items'][0]['first_name']} {info['items'][0]['last_name']}'
            link_fav = f'https://vk.com/id{str(id_favorit)}'
            photo_favorit = self.vk_user.photos.get(owner_id=id_favorit,album_id='profile', extended=1, photo_sizes=1)
            photo = [{'like': photo_favorit['items'][i]['likes']['count'],
                      'url': photo_favorit['items'][i]['sizes'][-1]['url']} for i in range(len(photo_favorit['items']))]
            newlist = sorted(photo, key=lambda d: d['like'])[::-1][:3]

            keyboard_prof = VkKeyboard(inline=True)
            keyboard_prof.add_openlink_button('Профиль', link_fav)
            self.vk.messages.send(user_id=id_vk,
                                  message=name,
                                  keyboard=keyboard_prof.get_keyboard(),
                                  random_id=0)
            for foto in newlist:
                self.send_photo(id_vk, *self.upload_photo(foto['url']))
                time.sleep(0.5)

            for event in self.longpoll.listen():
                if event.type == VkEventType.MESSAGE_NEW:
                    if event.to_me:
                        msg = event.text
                        id_vk = event.user_id
                        if msg == 'Далее':
                            break
                        elif msg == 'Добавить в избранное❤.':
                            return self.save_found_users(id_vk, id_favorit, name)
                        elif msg == 'Стоп!':
                            self.vk.messages.send(user_id=id_vk,
                                                  message='Для продолжения нажмите 👉 "Старт"',
                                                  keyboard=self.key_menu().get_keyboard(),
                                                  random_id=0)
                            return self.start_bot()

    def key_menu(self):
        button_menu=VkKeyboard()
        button_menu.add_button('Старт', VkKeyboardColor.POSITIVE)
        button_menu.add_button('Избранные❤', VkKeyboardColor.PRIMARY)
        button_menu.add_button('Что я могу?', VkKeyboardColor.SECONDARY)
        return button_menu
    def start_bot(self):
        while True:
            for event in self.longpoll.listen():
                text_start = ('Привет помогу тебе подобрать собеседника. '
                              'Для этого нажми кнопку Старт😀, а также могу показать тех кого ты'
                              'уже добавил в избранное😀!ну что начнем???😉'
                              '👇👇👇')
                try:
                    if event.type == VkEventType.MESSAGE_NEW:
                        if event.to_me:
                            msg = event.text
                            id_vk = event.user_id
                            if msg == 'Начать':
                                self.vk.messages.send(user_id=id_vk,
                                                      message=text_start,
                                                      keyboard=self.key_menu().get_keyboard(),
                                                      random_id=0)
                                try:
                                    self.session.add(VK_ID(id_user_vk=id_vk))
                                    self.session.commit()
                                except:
                                    pass

                            elif msg == 'Старт':
                                self.search_user(id_vk)

                            elif msg == 'Избранные❤':
                                self.send_users_from_favorite(id_vk=id_vk, favorits=self.get_users_from_favorite(id_vk))


                            elif msg == 'Что я могу?':
                                self.vk.messages.send(user_id=id_vk,
                                                      message=text_start,
                                                      keyboard=self.key_menu().get_keyboard(),
                                                      random_id=0)

                            else:
                                self.vk.messages.send(user_id=id_vk,
                                                      message='Не правильная команда. '
                                                            'Нажмите кнопку "Что я могу?"',
                                                      keyboard=self.key_menu().get_keyboard(),
                                                      random_id=0)
                except:
                    self.vk.messages.send(user_id=id_vk,
                                          message='Не правильная команда. '
                                                  'Нажмите кнопку "Что я могу?"',
                                          keyboard=self.key_menu().get_keyboard(),
                                          random_id=0)


    #дописать что бы выводила айди
    def save_found_users(self, id_user_vk, id_user_favorit, name):
        try:
            self.session.add(Favorits(id_favorit_vk=id_user_favorit))
            self.session.commit()
            user_id_vk = self.session.query(VK_ID).filter(VK_ID.id_user_vk == id_user_vk).first()
            favorit_id = self.session.query(Favorits).filter(Favorits.id_favorit_vk == id_user_favorit).first()
            print(user_id_vk.id_user)
            print(favorit_id.id_favorit)
            self.session.add(VK_Favorit(id_user_vk=user_id_vk.id_user, id_favorit_vk=favorit_id.id_favorit))
            self.session.commit()

            self.vk.messages.send(user_id=id_user_vk,
                                  message=f'{name} добавлен(а) в избранное! Для продолжение нажмите Старт'
                                          f' или посмотрите кто у вас в избранном!',
                                  keyboard=self.key_menu().get_keyboard(),
                                  random_id=0)

        except:
            self.vk.messages.send(user_id=id_user_vk,
                                  message=f'{name} уже у вас в избранном!',
                                  random_id=0)



    def get_users_from_favorite(self, id_vk_user):
        favorit_list = []

        user_id_vk = self.session.query(VK_ID.id_user).filter(VK_ID.id_user_vk == id_vk_user).first()
        query = self.session.query(Favorits.id_favorit_vk).select_from(Favorits). \
            join(VK_Favorit, VK_Favorit.id_favorit_vk == Favorits.id_favorit). \
            filter(VK_Favorit.id_user_vk == user_id_vk.id_user)
        for idfav in query.all():
            favorit_list.append(idfav[0])
        return favorit_list

    def send_users_from_favorite(self, id_vk, favorits):

        if len(favorits) >= 1:
            text_ = ''
            for id_fav in favorits:
                info_favorit = self.vk.users.get(user_ids=id_fav)
                name = f'{info_favorit[0]["first_name"]} {info_favorit[0]["last_name"]}'
                link = f'id{str(id_fav)}'
                text_ += f'[{link}|{name}]\n'
            self.vk.messages.send(user_id=id_vk,
                                  message=text_,
                                  keyboard=self.key_menu().get_keyboard(),
                                  random_id=0)



        else:
            self.vk.messages.send(user_id=id_vk,
                                  message='К сожалению вы еще не кого не добавили в избранное!',
                                  keyboard=self.key_menu().get_keyboard(),
                                  random_id=0)

