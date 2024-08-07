import yaml
import sqlalchemy
from sqlalchemy.orm import sessionmaker
from modelsdb.model import create_tables, drop_tables
from classVK.vk import VK

try:
    from yaml import CLoader as Loader
except ImportError:
    from yaml import Loader


if __name__ == '__main__':
    settings_dict = {}
    stream = open("settings.yaml", 'r', encoding="utf-8")
    settings_dict = yaml.load(stream, Loader)

    db_user = str(settings_dict["db"]["db_user"])
    db_pass = str(settings_dict["db"]["db_pass"])
    db_host = str(settings_dict["db"]["db_host"])
    db_port = str(settings_dict["db"]["db_port"])
    db_name = str(settings_dict["db"]["db_name"])

    DSN = f"postgresql://{db_user}:{db_pass}@{db_host}:{db_port}/{db_name}"

    engine = sqlalchemy.create_engine(DSN)

#Удалить сенд месседж в обработке возраста и города
    Session = sessionmaker(bind=engine)
    session = Session()
    # drop_tables(engine)
    create_tables(engine)


    vk_token = str(settings_dict["vk"]["token"])
    vk_token_user = str(settings_dict["vk"]["token_user"])
    vk_obj = VK(token=vk_token, session=session, token_user=vk_token_user)

    vk_obj.start_bot()
