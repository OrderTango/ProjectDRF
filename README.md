# ProjectDRF

Pull branch

    `git pull origin drf-messaging-app`


Install all packages

    `cd ProjectDRF`

    `pip install requirements.txt`
    
    `python manage.py/runserver`
    

Open another terminal under ProjectDRF directory

    `cd __shared__/frontend/chat`

    `npm install`



To build Angular Project 

    under `__shared__/frontend/chat` directory

        `ng build --watch`
        
 
Logged user first in `localhost:8000`

Open it to another tab and enter:
 
`http://customer12.localhost:8000/chat`

Reminder:
`http://customer12.localhost:8000/` was hardcoded in the frontend where `customer12` is the returned schema domainUrl from
django. If the domainUrl is not the same with `customer12`, the app especially on the frontend won't work.




 


