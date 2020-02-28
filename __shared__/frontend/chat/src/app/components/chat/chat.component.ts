import { Component, OnInit } from '@angular/core';
import { FormGroup, FormControl, Validators } from '@angular/forms'
import { Router } from '@angular/router';

import { ChatService } from '../../services/chat.service';

@Component({
  selector: 'app-chat',
  templateUrl: './chat.component.html',
  styleUrls: ['./chat.component.sass']
})
export class ChatComponent implements OnInit {

  users = []
  rooms = []

  roomForm = new FormGroup({
    roomName: new FormControl(''),
  });

  constructor(
    private router: Router,
    private chatService: ChatService,
  ) { }

  ngOnInit(): void {
    this.chatService.getUsers().subscribe((res) => {
      this.users = Object(res);
    })

    this.chatService.getChatRooms().subscribe((res) => {
      console.log(res)
      this.rooms = Object(res)
    })
  }

  onKey(event) {
    if(event.keyCode === 13) {
      this.onSubmit();
    }
  }

  onSubmit() {
    this.chatService.createChatRoom(this.roomForm.value.roomName)
    .subscribe(res => {
      console.log(res)
      this.router.navigate([`/chat/`, this.roomForm.value.roomName])

      this.roomForm.reset()
    },
    error => {
      console.log(error)
    }
    )
  }

  // onSubmit(firstName, lastName) {
  //   var room_name = `${firstName}-${lastName}`

  //   this.rooms.forEach(room => {
  //     if(room === room_name) {
  //       this.router.navigate(['/chat', room_name])
  //     }else {
  //       this.chatService.createChatRoom(room_name).subscribe(res => {
  //         this.router.navigate([`/chat/`, room_name])
  //       }, 
  //       error => {
  //         console.log(error)
  //       })
  //     }
  //   })
  // }

}
