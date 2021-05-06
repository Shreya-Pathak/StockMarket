from locust import HttpUser, TaskSet, task
import json
from bs4 import BeautifulSoup
import string
import random
def print_msgs(rep):
    soup = BeautifulSoup(rep.text,'html.parser')
    txts=soup.find_all('div',{'class':'alert'})
    if len(txts)!=0:
        print([x.text.strip() for x in txts])

class QuickStartUser(HttpUser):
    

    def on_start(self):
        self.ws_printed=False
        self.signup()
        self.login()
        self.wishlist()
        # self.wishlist()


    def signup(self):
        response = self.client.get('signup')
        # print(response.cookies)
        csrftoken = response.cookies['csrftoken']
        letters = string.ascii_lowercase
        self.name=''.join(random.choice(letters) for i in range(10))
        rep=self.client.post('signup',
                         {'email': [f'{self.name}@dad.com'], 'password': [self.name],'name':[self.name],'address':['298D'],'telephone':['12888'] ,'client_signup':['Sign Up']},
                         headers={'X-CSRFToken': csrftoken}, allow_redirects=True)
        print_msgs(rep)

    def login(self):
        # login to the application
        response = self.client.get('login')
        # print(response.cookies)
        csrftoken = response.cookies['csrftoken']
        rep=self.client.post('login',
                         {'username': self.name, 'password': self.name,'client_login':'yes'},
                         headers={'X-CSRFToken': csrftoken}, allow_redirects=True)
        # print(dir(rep))
        # print_msgs(rep)

    @task
    def tmp(self):
        pass
    
    def wishlist(self):
        response = self.client.get('client/wishlists')
        csrftoken = response.cookies['csrftoken']
        rep=self.client.post('client/wishlists',{'wname':[f'Test{self.name}'],'stock':[random.randint(1,100)],'submit':['Update Wishlist']},headers={'X-CSRFToken': csrftoken},allow_redirects=True)
        # print(rep.text)
        if not(self.ws_printed):
            # self.ws_printed=True
            print(rep.cookies['msg'])
            

    # for i in range(4):
    #     # @task(2)
    #     def first_page(self):
    #         self.client.get('/list_page/')



    # @task(3)
    # def get_second_page(self):
    #     self.client.('/create_page/', {'name': 'first_obj'}, headers={'X-CSRFToken': csrftoken})


    # @task(4)
    # def add_advertiser_api(self):
    #     auth_response = self.client.post('/auth/login/', {'username': 'suser', 'password': 'asdf1234'})
    #     auth_token = json.loads(auth_response.text)['token']
    #     jwt_auth_token = 'jwt '+auth_token
    #     now = datetime.datetime.now()

    #     current_datetime_string = now.strftime("%B %d, %Y")
    #     adv_name = 'locust_adv' 
    #     data = {'name', current_datetime_string}
    #     adv_api_response = requests.post('http://127.0.0.1:8000/api/advertiser/', data, headers={'Authorization': jwt_auth_token})



# class ApplicationUser(HttpUser):
#     task_set = UserActions
#     min_wait = 0
#     max_wait = 0
