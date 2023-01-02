
import time
import socket
from threading import Thread
from typing import Union
import pickle
import os
import json
import sys
import random

class MyServer :

    ADDR = "localhost"
    PORT = 4567

    PicturePath = "Osmenia Pics"
    QuestionsFile = "Questions.json"
    questions : dict = None # { 'friend' : [] , 'love' : [] , 'talk' : [] }
    NicknamesFile = "Nicknames.json"
    nicknames : dict = None # { 'male' : [] , 'female' : [] }
    QoutesFile = "Qoutes.json"
    qoutes : list = None # []

    connected = 100
    BYTE = 16

    server : socket.socket = None

    males : list[tuple[socket.socket, str]] = []
    females : list[tuple[socket.socket, str]] = []

    users : list[str] =[]

    def creat_server(self):
        self.server = socket.socket(socket.AF_INET , socket.SOCK_STREAM)
        self.server.bind((self.ADDR , self.PORT))

    def accept_users(self):
        self.server.listen(self.connected)
        self.ready_the_datas()
        Thread(target=self.partnering_clients , args=(1,3)).start()

        while True:
            client , addr = self.server.accept()
            Thread(target=self.process_user , args=(client , addr)).start()

    def process_user(self, client : socket.socket , addr : str):
        # { "id" : self.parent.appData.get_id() , "find" : gender , "question" : question }
        data = self.recieved_data(client)
        if not data:
            client.close()
            return
        self.users.append(data["id"])

        if data["find"] == "M" :
            self.females.append( (client , data["question"]) )
        else :
            self.males.append((client, data["question"]))

    def partnering_clients(self, algo = 1 , delay = 3):
        # Delay 3 second then if not found partner then close the socket
        if algo != 1 :
            while True:
                time.sleep(delay)
                if not self.males and not self.females:
                    pass
                elif not self.females and self.males:
                    male = self.males[0]
                    self.males.remove(male)
                    Thread( target=self.skip_client , args=(male,)).start()
                elif not self.males and self.females:
                    female = self.females[0]
                    self.females.remove(female)
                    Thread(target=self.skip_client , args=(female,)).start()
                else:
                    male = self.males[0]
                    female = self.females[0]
                    self.males.remove(male)
                    self.females.remove(female)
                    Thread(target=self.giving_data_to_partner, args=(male, female)).start()

        # Without delay and move until found
        while True:
            if not self.males or not self.females:
                pass
            else:
                male = self.males[0]
                female = self.females[0]
                self.males.remove(male)
                self.females.remove(female)
                Thread(target=self.giving_data_to_partner , args=(male , female)).start()
                time.sleep(.5)

    def skip_client(self, client : tuple[socket.socket , str]):
        data = { 'find' : 'Cant Find Partner'}
        self.send_data(client[0] , data)
        client[0].close()

    def giving_data_to_partner(self, partner : tuple[tuple[socket.socket, str] , tuple[socket.socket, str] ]):
        # { "nickname" : tuple ( finder , finding ) , "pic data" : pic_data , "pic ext" : ext , "questions" : questions [list] , "qoute" : qoute }
        nickname = self.get_nickname()
        qoute = self.get_qoutes()
        male_quest = self.get_questions(partner[0][1])
        fem_quest = self.get_questions(partner[1][1])
        pic_data , pic_ext = self.get_place()

        male = { 'nickname' : (nickname[0] , nickname[1]) , 'pic data' : pic_data , 'pic_ext' : pic_ext , 'questions' : male_quest , 'qoute' : qoute }
        female = {'nickname': (nickname[1], nickname[0]), 'pic data': pic_data, 'pic_ext': pic_ext, 'questions': fem_quest, 'qoute': qoute}

        try :
            self.send_data(partner[0][0], male)
        except OSError:
            partner[0][0].close()

        try :
            self.send_data(partner[1][0] , female)
        except OSError:
            partner[1][0].close()

    def get_place(self):
        selected =  random.sample(os.listdir(self.PicturePath) , k=1)
        path = os.path.join(os.getcwd() , selected)
        with open(path , 'rb' ) as file :
            pic_data = file.read()
        pic_ext : str = os.path.splitext(selected)[1]
        return (pic_data , pic_ext )

    def get_questions(self, q_type):
        questions = random.sample(self.questions[q_type] , k=10)
        return questions

    def get_qoutes(self):
        index = random.randint(0 , len(self.qoutes) - 1 )
        return self.qoutes[index]

    def get_nickname(self):
        index = random.randint(0 , len(self.nicknames) -1)
        return ( self.nicknames['maled'][index] , self.nicknames['female'][index] )

    def recieved_data(self, client : socket.socket) -> Union[None , dict] :
        datas : list[bytes] = []
        while True :
            try:
                data : bytes = client.recv(self.BYTE)
                if not data :
                    break
            except OSError :
                return None
        try :
            return json.loads(b"".join(datas))
        except pickle.PickleError :
            return  None

    def send_data(self, client : socket.socket, data : dict) -> bool:
        data = pickle.dumps(data)
        try :
            client.sendall(data)
        except OSError :
            return False
        else:
            return True

    def ready_the_datas(self):
        os.makedirs(self.PicturePath, exist_ok=True)
        if len(os.listdir(self.PicturePath)) < 1 :
            raise FileExistsError(f"{self.PicturePath} is empty")
        if not os.path.exists(self.QuestionsFile) :
            raise FileNotFoundError(f"{self.QuestionsFile} is not found")
        if not os.path.exists(self.NicknamesFile):
            raise FileNotFoundError(f"{self.NicknamesFile} is not found")
        if not os.path.exists(self.QoutesFile) :
            raise FileNotFoundError(f"{self.QoutesFile} is not found")

        try :
            with open(self.QuestionsFile , 'r') as jf :
                self.questions = json.load(jf)
        except json.JSONDecodeError as e :
            print(e)
            sys.exit()
        try:
            with open(self.NicknamesFile, 'r') as jf:
                self.nicknames = json.load(jf)
        except json.JSONDecodeError as e:
            print(e)
            sys.exit()
        try:
            with open(self.QoutesFile, 'r') as jf:
                self.qoutes = json.load(jf)
        except json.JSONDecodeError as e:
            print(e)
            sys.exit()


if __name__ == "__main__" :
    test = MyServer()
    test.creat_server()
    test.accept_users()

