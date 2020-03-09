import { OnChanges, SimpleChanges, Component, OnInit, ElementRef, EventEmitter, ViewChild, Input, Output } from '@angular/core';
import { FormGroup, FormControl } from '@angular/forms';
import { ActivatedRoute, Router } from '@angular/router';
import { NgbModal, NgbModalRef, NgbDropdown } from '@ng-bootstrap/ng-bootstrap';
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
  @Output() roomHasMessage = new EventEmitter<boolean>();

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
  addedMembers = [];
  roomMembers = [];
  roomNewName: String = '';

  addMemberModalRef: NgbModalRef;

  constructor(
    private activatedRoute: ActivatedRoute,
    private router: Router,
    private modal: NgbModal,
    private chatService: ChatService,
  ) { }

  ngOnInit(): void {
    
    this.chatService.getUser().subscribe((res) => {
      this.chatUser = res.userId
    })

    this.chatService.getUsers().subscribe((res) => {
      this.users = Object(res);
    })

    this.getChatRoom(this.room_name)
    this.transformRoomName(this.room_name)
    this.messageForm.reset();
  }

  ngOnChanges(changes: SimpleChanges) {
    this.room_name = changes.room_name.currentValue;
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
        var message = []
        message = this.messages[0];
        console.log(message['members'])

        this.roomMembers = message['members'];
        
        if(this.messages.length === 0) {
          this.hasMessages = false;
          this.roomHasMessage.emit(this.hasMessages)
        }else{
          this.hasMessages = true;
          console.log('HERE 1', this.roomHasMessage.emit(this.hasMessages))
        }

      }else {
        this.messages.push(data['message']); 

        if(this.messages.length === 0) {
          this.hasMessages = false;
          this.roomHasMessage.emit(this.hasMessages)
        }else{
          this.hasMessages = true;
          this.roomHasMessage.emit(this.hasMessages)
          console.log(this.roomHasMessage.emit(this.hasMessages))
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

  autoGrow() {
    const textArea = this.textArea.nativeElement;

    textArea.style.overflow = 'scroll';
    textArea.style.height = '0px';
    textArea.style.height = textArea.scrollHeight + 'px';
  }

  onKey(event) {
    if(event.keyCode === 13) {
      this.onSubmit();
    }
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

  addMemberModal(template) {
    this.addMemberModalRef = this.modal.open(template, { backdrop: true, size: 'lg'})
  } 

  closeMemberModal() {
    this.addMemberModalRef.close()
  }

  selectedMember(user) {
    if(user.userId !== this.chatUser) {
      if(!this.addedMembers.some((m) => m.userId == user.userId)) {
        this.addedMembers.push({'userId': user.userId, 'firstName': user.firstName, 'lastName': user.lastName, 'email': user.email})
      }
    }
  }

  addMember() {
    this.chatSocket.send(JSON.stringify({
      'thread': this.room_name,
      'command': 'new_member',
      'members': this.addedMembers
    }))
  }

  removeAddedMember(id) {
    this.addedMembers = this.addedMembers.filter(room => room.id !== id);
  }

}
