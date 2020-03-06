import { Component, OnInit } from '@angular/core';
import { FormGroup, FormControl, Validators } from '@angular/forms'
import { Router } from '@angular/router';

import { ChatService } from '../../services/chat.service';

@Component({
  selector: 'app-chat',
  templateUrl: './chat.component.html',
  styleUrls: ['./chat.component.css']
})
export class ChatComponent implements OnInit {

  authUser = null;
  users = []
  rooms = []
  createRoom: Boolean = false;
  isChatRoom: Boolean = true;
  chat_room: String = '';
  chat_room_name: String = '';
  chat_id = null;

  roomForm = new FormGroup({
    roomName: new FormControl(''),
  });

  constructor(
    private router: Router,
    private chatService: ChatService,
  ) { }

  ngOnInit(): void {
    this.chatService.getUser().subscribe((res) => {
      this.authUser = res;
    })

    this.chatService.getUsers().subscribe((res) => {
      this.users = Object(res);
    })

    this.chatService.getChatRooms().subscribe((res) => {
      this.rooms = Object(res);

      this.rooms.forEach(r => {
        // Transform user-named thread name
        if(r.name.match(/[A-Z][a-z]+|[0-9]+/g)) {
          if(!(/\d/.test(r.name))) {
            var name = r.name.match(/[A-Z][a-z]+|[0-9]+/g).join(" ")
            r['temp_name']=name;
          }else{
            r['temp_name']=r.name;
          }
        }else{
          r['temp_name']=r.name;
        }
      })

      console.log(this.rooms)

      if(this.chat_room=== '') {
        var chat = this.rooms.slice(-1)[0];
        this.chat_room = chat.name;
        this.chat_room_name = chat.temp_name;
      }
    })
  }

  onKey(event) {
    if(event.keyCode === 13) {
      this.submitChatRoom();
    }
  }

  createChatRoom(firstName, lastName) {
    this.chat_room = `${firstName}${lastName}`;
    console.log('Here 1: ', this.chat_room)
  }

  submitChatRoom() {
    this.chat_room= this.roomForm.value.roomName;
    console.log('Here 2: ', this.chat_room)
    this.roomForm.reset();

    // this.chatService.createChatRoom(this.authUser.userId, this.roomForm.value.roomName)
    // .subscribe(res => {
    //   console.log(res)
    // this.router.navigate([`/chat/`, this.roomForm.value.roomName])

    //   this.roomForm.reset()
    // },
    // error => {
    //   console.log(error)
    // }
    // )
  }

  selectChatRoom(room_name) {
    this.chat_room = room_name;
    console.log('Here 3: ', this.chat_room)
  }

  deleteChatRoom(room) {
    this.chatService.deleteChatRoom(room).subscribe(res => {
      console.log(res)
      this.chat_room = '';
    }, error => {
      console.log(error)
    })
  }
}
