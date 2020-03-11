import { Injectable } from '@angular/core';
import { Headers, Http } from '@angular/http';
import { HttpClient, HttpHeaders } from '@angular/common/http';
import { Observable } from 'rxjs';

@Injectable({
  providedIn: 'root'
})
export class ChatService {
  csrfToken = null;
  // baseurl = "http://customer12.localhost:8000"; // window.location.pathname

  baseurl = "http://ragavi2113.localhost:8000"; // window.location.pathname

  constructor(
    private http: Http,
    private httpClient: HttpClient,
  ) { }

  getUsers(): Observable<any> {
    return this.httpClient.get(`${this.baseurl}/api/accounts/`, this.getHeader())
  }

  getUser(): Observable<any> {
    return this.httpClient.get(`${this.baseurl}/api/user/account/`, this.getHeader())
  }

  getOrg(id): Observable<any> {
    console.log('HERE HERE: ', id)
    return this.httpClient.get(`${this.baseurl}/api/org/${id}/`, this.getHeader())
  }

  getChatRooms(): Observable<any> {
    return this.httpClient.get(`${this.baseurl}/api/thread/`, this.getHeader())
  }

  deleteChatRoom(id): Observable<any> {
    console.log('DELETE THREAD: ', id)
    return this.httpClient.delete(`${this.baseurl}/api/thread/${id}/`, this.getHeader())
  }

  removeRoomMember(room, id): Observable<any> {
    return this.httpClient.delete(`${this.baseurl}/api/${room}/${id}/members/`, this.getHeader())
  }

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
