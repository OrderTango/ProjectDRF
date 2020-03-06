import { OnChanges, SimpleChanges, Component, OnInit, ElementRef, ViewChild, Input } from '@angular/core';
import { FormGroup, FormControl } from '@angular/forms';
import { ActivatedRoute, Router } from '@angular/router';
import * as ReconnectingWebSocket from 'src/assets/reconnecting-websocket.js';

import { ChatService } from '../../services/chat.service';

@Component({
  selector: 'app-chat-room',
  templateUrl: './chat-room.component.html',
  styleUrls: ['./chat-room.component.css']
})
export class ChatRoomComponent implements OnInit, OnChanges {

  @ViewChild('textArea') textArea: ElementRef;
  @ViewChild('messageArea') messageArea: ElementRef;
  @Input() room_name: string;

  messageForm = new FormGroup({
    content: new FormControl(''),
    messageContent: new FormControl(''),
  })

  private chatSocket;
  // private roomName: string;
  private chatUser: string;
  private socketMessages = [];
  isAuthUser: boolean;
  hasChatRoom: boolean = false;
  hasMessages: boolean = false;
  messages = [];
  users = [];
  roomMembers = [];
  roomNewName: String = '';

  constructor(
    private activatedRoute: ActivatedRoute,
    private router: Router,
    private chatService: ChatService,
  ) { }

  ngOnInit(): void {
    // this.roomName = this.activatedRoute.snapshot.paramMap.get('room_name');
    this.chatService.getUser().subscribe((res) => {
      this.chatUser = res.userId
    })

    this.getChatRoom(this.room_name)
    this.transformRoomName(this.room_name)
    this.messageForm.reset();
  }

  ngOnChanges(changes: SimpleChanges) {
    var room_name = changes.room_name.currentValue;
    this.getChatRoom(room_name)
    this.transformRoomName(room_name)
  }

  transformRoomName(room_name) {
    if(room_name.match(/[A-Z][a-z]+|[0-9]+/g)) {
      if(!(/\d/.test(room_name))) {
        var name = room_name.match(/[A-Z][a-z]+|[0-9]+/g).join(" ")
        this.roomNewName = name;
      }else{
        this.roomNewName = room_name;
      }
    }else{
     this.roomNewName = room_name;
    }
  }

  getChatRoom(room_name) {
    if(room_name === '' || room_name === undefined) {
      this.hasChatRoom = false;
    }else {
      this.hasChatRoom = true;
      this.createWebSocket(room_name);

      // this.chatService.getChatMembers(room_name).subscribe((res) => {
      //   this.roomMembers = Object(res);
      //   console.log(this.roomMembers);
      // })
    }
  }

  createWebSocket(room_name) {
    this.chatSocket = new ReconnectingWebSocket (
      `ws://customer12.localhost:8000/ws/api-chat/${room_name}/` 
    )
    this.chatSocket.debug = true;

    this.chatSocket.onopen = (e) => {
      this.fetchMessages();
    }

    this.chatSocket.onmessage = (e) => {

      var data = JSON.parse(e.data);
      let command = data['command'];

      if(command === 'fetch_message') {
        this.messages = data['message']
        
        if(this.messages.length === 0) {
          this.hasMessages = false;
        }else{
          this.hasMessages = true;
        }

      }else {
        this.messages.push(data['message']); 

        if(this.messages.length === 0) {
          this.hasMessages = false;
        }else{
          this.hasMessages = true;
        }
      }
    }

    this.chatSocket.onclose = (e) => {
      console.error('Chat socket closed unexpectedly');
    }
  }

  fetchMessages() {
    this.chatSocket.send(JSON.stringify({
      'from': this.chatUser,
      'command': 'fetch_message'
    }))
  }

  onKey(event) {
    if(event.keyCode === 13) {
      this.onSubmit();
    }
  }

  autoGrow() {
    const textArea = this.textArea.nativeElement;

    textArea.style.overflow = 'scroll';
    textArea.style.height = '0px';
    textArea.style.height = textArea.scrollHeight + 'px';
  }

  onSubmit() {
    var message = this.messageForm.value.content; 

    console.log(this.chatUser)

    this.chatSocket.send(JSON.stringify({
      'message': message,
      'command': 'new_message',
      'from': this.chatUser
    }));

    this.messageForm.reset();
    const textArea = this.textArea.nativeElement;
    textArea.style.height = '54px';
  }

  back() {
    this.router.navigate([`/chat`])
  }

}
