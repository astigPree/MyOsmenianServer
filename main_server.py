
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
    pictures : list = [] # [ ( bytes , ext ) ]
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

    def create_server(self):
        self.server = socket.socket(socket.AF_INET , socket.SOCK_STREAM)
        self.server.bind((self.ADDR , self.PORT))
        print("[/] Server is created")

    def accept_users(self):
        self.server.listen(self.connected)
        print("[/] Server is ready to listen")
        self.ready_the_datas()
        print("[/] Datas is imported")
        Thread(target=self.partnering_clients_v3 ).start()
        print(f"\n[/] Accepting clients")
        while True:
            try:
                client , addr = self.server.accept()
            except  (BlockingIOError, TimeoutError, InterruptedError) as err:
                print(f"[!] Error Occur : {err}")
            else:
                print(f"Client address : {addr}")
                Thread(target=self.process_user , args=(client , addr)).start()

    def process_user(self, client : socket.socket , addr : str):
        # { "id" : self.parent.appData.get_id() , "find" : gender , "question" : question }
        data = self.recieved_data(client)
        print(data)
        if not data:
            client.close()
            return
        self.users.append(data["id"])

        if data["find"] == "M" :
            self.females.append( (client , data["question"]) )
        else :
            self.males.append((client, data["question"]))
        print("Done adding to respective gender")

    def partnering_clients_v1(self , algo = 2 , delay = 3):
        # Delay a second then if not found partner then close the socket
        print(f"[/] Partnering is running")
        if algo == 2 :
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

    def partnering_clients_v2(self , algo = 1):
        # Without delay and move until found
        if algo == 1 :
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

    def partnering_clients_v3(self):
        # Set the time where the user can escape in the server
        second_pass = 0
        limit = 5
        while True:

            # If females is empty then some male move to female HAHHAHAAH
            if len(self.males) > 10 and not self.females:
                male = self.males[0]
                self.males.remove(male)
                self.females.append(male)
            elif len(self.females) > 10 and not self.males:
                female = self.females[0]
                self.females.remove(female)
                self.males.append(female)
            else:
                pass

            # Partnering logic
            if not self.males and not self.females:
                pass
            elif self.males and not self.females :
                if second_pass == limit:
                    male = self.males[0]
                    self.males.remove(male)
                    Thread(target=self.skip_client, args=(male,)).start()
                    second_pass = 0
                else:
                    print(f"Male : {second_pass}")
                    second_pass = second_pass + 1
                    time.sleep(1)
            elif not self.males and self.females:
                if second_pass == limit:
                    female = self.females[0]
                    self.females.remove(female)
                    Thread(target=self.skip_client , args=(female,)).start()
                    second_pass = 0
                else:
                    print(f"Female : {second_pass}")
                    second_pass = second_pass + 1
                    time.sleep(1)
            else :
                second_pass = 0
                male = self.males[0]
                female = self.females[0]
                self.males.remove(male)
                self.females.remove(female)
                Thread(target=self.giving_data_to_partner, args=( (male, female) , ) ).start()

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
        pic_data , pic_ext = self.get_place_randomly()

        male = { 'nickname' : (nickname[0] , nickname[1]) , 'pic data' : pic_data , 'pic ext' : pic_ext , 'questions' : male_quest , 'qoute' : qoute }
        female = {'nickname': (nickname[1], nickname[0]), 'pic data': pic_data, 'pic ext': pic_ext, 'questions': fem_quest, 'qoute': qoute}
        print("Sending data to partners")

        # Send data to male client
        if not self.send_data(partner[0][0] , male):
            partner[0][0].close()
            # if not sent then send 'Partner Left' to female client then end activity
            female = {'find': 'Partner Left'}
            self.send_data(partner[1][0] , female)
            partner[1][0].close()
            return

        # If sent then send the data to female
        if not self.send_data(partner[1][0] , female):
            partner[1][0].close()
            # if not sent then send 'Partner Left' to male client then end activity
            male = {'find': 'Partner Left'}
            self.send_data(partner[1][0] , male)
            partner[1][0].close()
            return

        # If sent then send 'done' to male client
        male = { 'done': 'done'}
        self.send_data(partner[0][0] , male)
        partner[0][0].close()
        partner[1][0].close()
        return

    def get_place_randomly(self):
        index = random.randint(0 , len(self.pictures) - 1)
        return self.pictures[index]

    def get_questions(self, q_type):
        questions = random.sample(self.questions[q_type] , k=10)
        return questions

    def get_qoutes(self):
        index = random.randint(0 , len(self.qoutes) - 1 )
        return self.qoutes[index]

    def get_nickname(self):
        index = random.randint(0 , len(self.nicknames['male']) -1)
        return ( self.nicknames['male'][index] , self.nicknames['female'][index] )

    def recieved_data(self, client : socket.socket) -> Union[None , dict] :
        datas : list[bytes] = []
        try:
            while True:
                data : bytes = client.recv(self.BYTE)
                datas.append(data)
                if user_data := self.checking(datas):
                    return user_data
        except OSError :
            return None
        except ConnectionResetError :
            return None
        except Exception:
            return None

    def checking(self , datas : list):
        try :
            return pickle.loads(b"".join(datas))
        except pickle.PickleError :
            return  None

    def send_data(self, client : socket.socket, data : dict) -> bool:
        data = pickle.dumps(data)
        try :
            client.sendall(data)
        except OSError :
            return False
        except Exception :
            return False
        else:
            return True

    def get_place(self , selected : str):
        path = os.path.join(os.getcwd(), selected)
        with open(path, 'rb') as file:
            pic_data = file.read()
        pic_ext: str = os.path.splitext(selected)[1]
        return (pic_data, pic_ext[1:])

    def ready_the_datas(self):
        os.makedirs(self.PicturePath, exist_ok=True)
        if not os.path.exists(self.QuestionsFile) :
            raise FileNotFoundError(f"{self.QuestionsFile} is not found")
        if not os.path.exists(self.NicknamesFile):
            raise FileNotFoundError(f"{self.NicknamesFile} is not found")
        if not os.path.exists(self.QoutesFile) :
            raise FileNotFoundError(f"{self.QoutesFile} is not found")
        if len(os.listdir(self.PicturePath)) < 1 :
            raise FileExistsError(f"{self.PicturePath} is empty")
        for file in os.listdir(self.PicturePath):
            self.pictures.append(self.get_place( os.path.join(self.PicturePath , file) ) )

        try :
            with open(self.QuestionsFile , 'r') as jf :
                self.questions = json.load(jf)
        except json.JSONDecodeError as e :
            print(f"{self.QuestionsFile} error : {e}")
            sys.exit()
        try:
            with open(self.NicknamesFile, 'r') as jf:
                self.nicknames = json.load(jf)
        except json.JSONDecodeError as e:
            print(f"{self.NicknamesFile} error : {e}")
            sys.exit()
        try:
            with open(self.QoutesFile, 'r') as jf:
                self.qoutes = json.load(jf)
        except json.JSONDecodeError as e:
            print(f"{self.QoutesFile} error : {e}")
            sys.exit()

        # print(self.qoutes)
        # print(self.questions)
        #print(self.nicknames)
        #print(self.pictures)



if __name__ == "__main__" :
    test = MyServer()
    test.create_server()
    test.accept_users()

