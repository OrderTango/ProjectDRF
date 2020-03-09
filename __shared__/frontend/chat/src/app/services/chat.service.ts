import { Injectable } from '@angular/core';
import { Headers, Http } from '@angular/http';
import { HttpClient, HttpHeaders } from '@angular/common/http';
import { Observable } from 'rxjs';

@Injectable({
  providedIn: 'root'
})
export class ChatService {
  csrfToken = null;
  baseurl = "http://customer12.localhost:8000"; // window.location.pathname

  // baseurl = "http://ot4a1fcb01.localhost:8000"; // window.location.pathname

  constructor(
    private http: Http,
    private httpClient: HttpClient,
  ) { }


  getUsers(): Observable<any> {
    return this.httpClient.get(`${this.baseurl}/api-accounts`, this.getHeader())
  }

  getUser(): Observable<any> {
    return this.httpClient.get(`${this.baseurl}/api-user-account/`, this.getHeader())
  }

  getChatRooms(): Observable<any> {
    return this.httpClient.get(`${this.baseurl}/api/thread/`, this.getHeader())
  }

  deleteChatRoom(id): Observable<any> {
    console.log('DELETE THREAD: ', id)
    return this.httpClient.delete(`${this.baseurl}/api/thread/${id}/`, this.getHeader())
  }

  getChatMembers(room_name): Observable<any> {
    return this.httpClient.get(`${this.baseurl}/api/thread/${room_name}/members/`, this.getHeader())
  }
  // createChatRoom(creator, room_name): Observable<any> {
  //   return this.httpClient.post(`${this.baseurl}/api-chat/`, {'creator': creator, 'room_name': room_name}, this.getHeader())
  // }

  // createMessage(room_name, message_content): Observable<any> {
  //   return this.httpClient.post(`${this.baseurl}/api-chat/${room_name}`, {'content': message_content}, this.getHeader())
  // }

  // getMessages(room_name): Observable<any> {
  //   return this.httpClient.get(`${this.baseurl}/api-chat/${room_name}`, this.getHeader())
  // }

  getCSRFToken(name) {
    var xsrfCookies = document.cookie.split(';')
    .map(c => c.trim())
    .filter(c => c.startsWith(name + '='));

    if(xsrfCookies.length === 0) {
      return null;
    }

    return decodeURIComponent(xsrfCookies[0].split('=')[1]);
  }

  getHeader() {
    const httpHeaders = new HttpHeaders({
      'X-CSRFToken': this.getCSRFToken('csrftoken'),
      'Access-Control-Allow-Origin': '*',
      'Accept': 'application/json',
      'Content-Type': 'application/json'
    });

    const options = {headers: httpHeaders}
    return options
  }

}
