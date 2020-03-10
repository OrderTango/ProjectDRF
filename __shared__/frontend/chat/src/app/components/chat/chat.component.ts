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
  roomMessage = [];
  authUser = null;
  organization = null;
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
      console.log('fsdfsdfs', this.authUser)

      this.chatService.getOrg(this.authUser.userId).subscribe((res) => {
        this.organization = res;
        console.log('ORGANIZATION: ', this.organization)
      })
    })

    this.chatService.getUsers().subscribe((res) => {
      this.users = Object(res);
    })

    this.chatService.getChatRooms().subscribe((res) => {
      this.rooms = Object(res);

      console.log('Rooms: ', this.rooms)

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
    // this.rooms.push({id: '#', name: this.chat_room, date_created: "###", is_archived: false, temp_name: this.chat_room})
    console.log('Here 1: ', this.chat_room)
  }

  submitChatRoom() {
    this.chat_room= this.roomForm.value.roomName;
    // this.rooms.push({id: '#', name: this.chat_room, date_created: "###", is_archived: false, temp_name: this.chat_room})
    this.roomForm.reset();
    this.createRoom = false;
  }

  selectChatRoom(room_name) {
    this.chat_room = room_name;
    console.log('Here 3: ', this.chat_room)
  }

  deleteChatRoom(id) {
    this.chatService.deleteChatRoom(id).subscribe(res => {
      this.rooms = this.rooms.filter(room => room.id !== id);
      var chat = this.rooms.slice(-1)[0];
      this.chat_room = chat.name;
      this.chat_room_name = chat.temp_name;
    }, error => {
      console.log(error)
    })
  }

  getRoomMessage(message: any) {
    this.roomMessage = message; 

    // if(this.roomMessage.length !== 0) {
    //   if(!this.rooms.some((r) => r.id == this.roomMessage['thread_id'])) {
    //     this.rooms.push({id: this.roomMessage['thread_id'], name: this.roomMessage['thread'], date_created: this.roomMessage['date_created'], is_archived: false, temp_name: this.roomMessage['thread']})
    //   }
    // }

    // console.log(this.rooms)
    // console.log('Room Message: ', this.roomMessage);
  }
}
