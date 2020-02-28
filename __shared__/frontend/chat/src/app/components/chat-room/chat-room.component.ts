import { Component, OnInit } from '@angular/core';
import { FormGroup, FormControl } from '@angular/forms';
import { ActivatedRoute } from '@angular/router';

import { ChatService } from '../../services/chat.service';

@Component({
  selector: 'app-chat-room',
  templateUrl: './chat-room.component.html',
  styleUrls: ['./chat-room.component.sass']
})
export class ChatRoomComponent implements OnInit {
  messageForm = new FormGroup({
    content: new FormControl(''),
    messageContent: new FormControl(''),
  })

  private chatSocket;
  private roomName: string;
  private socketMessages = [];

  constructor(
    private activatedRoute: ActivatedRoute,
    private chatService: ChatService,
  ) { }

  ngOnInit(): void {
    this.roomName = this.activatedRoute.snapshot.paramMap.get('room_name');

    console.log(window.location.host)

    this.chatSocket = new WebSocket (
      `ws://customer12.localhost:8000/ws/chat/${this.roomName}/` 
    )

    // this.chatSocket = new WebSocket (
    //   'ws://' + window.location.host +
    //     '/ws/chat/' + this.roomName + '/'
    // )
    
    // this.chatService.getMessages(this.roomName)
    // .subscribe((res) => {
    //   console.log(res)
    // })
    
    this.chatSocket.onmessage = (e) => {
      var data = JSON.parse(e.data);
      var message = data['message'];

      this.socketMessages.push(`${message}`);
      this.messageForm.controls['messageContent'].setValue(`${this.socketMessages.join('\n')}`);
    } 

    this.chatSocket.onClose = (e) => {
      console.error('Chat socket closed unexpectedly');
    }
  }

  onKey(event) {
    if(event.keyCode === 13) {
      this.onSubmit();
    }
  }

  onSubmit() {
    var message = this.messageForm.value.content; 

    this.chatService.createMessage(this.roomName, message)
    .subscribe(res => {
      console.log(res)
    })

    this.chatSocket.send(JSON.stringify({
      'message': message
    }));

    this.messageForm.reset();
  }

}
