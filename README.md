# ProjectDRF


## A. SETTING UP THE DJANGO PROJECT 


a1. Pull branch

    `git pull origin drf-messaging-app`


a2. Create virtual environment and activate it (would be better if you create it outside the project directory. Just create a folder and transfer the project inside)


a3. Install all packages inside the project.

    `cd ProjectDRF` 

    `pip install requirements.txt`


a4. Install redis on your computer and run it.
    

a5. Run server.

    `python manage.py/runserver`



## B. SETTING UP THE ANGULAR PROJECT


b1. Make sure that you have installed node and npm in your computer.


b2. Install angular cli in your computer.

    `npm install -g @angular/cli@9.0.3`


b3. Open another terminal under ProjectDRF directory.


b4. Go to frontend project and install all the packages.

    `cd __shared__/frontend/chat`

    `npm install`


b5. Build the Angular project.

    `ng build --watch`



## C. TO CREATE AND LOGIN USER AND SUBUSER


c1. Go to `localhost:8000`


c2. Click `Signup` to create user.


c3. After receiving an email, enter the `OTP` code you recieved and enter it on your previous page (`localhost:8000`) to validate.


c4. After validate, click `On Board` then login.


c5. Create domain name for your site.


c6. Go to `User Adminitration` > `View User`.


c7. From there, click `Create User` and create a sub user.


c8. To login subuser, logout first from your current user and login subuser using the domain you created:

    e.g. `<domain-name>.localhost:8000/login/`



## D. USING THE APP


d1. Copy the url of your current page and replace the url after `8000/` with `chat/` to another tab.
 
    e.g. `http://<domain-name>.localhost:8000/chat`


d2. Click `Create` beside the `Chats` header.


d3. Enter the name of your thread (no spaces).


d4. You can also create thread by clicking any of the members under `Contacts`.


d6. To create a message, enter any message on the `Enter message..` input box and click `Send`.


d7. To add member, click `Add Member`.





 


