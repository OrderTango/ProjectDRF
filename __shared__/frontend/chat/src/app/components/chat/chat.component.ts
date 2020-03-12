import { Component, OnInit } from '@angular/core';
import { FormGroup, FormControl, Validators } from '@angular/forms'
import { Router } from '@angular/router';
import { NgbModal, NgbModalRef, NgbDropdown } from '@ng-bootstrap/ng-bootstrap';

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
  subUsers = []
  rooms = []
  createRoom: Boolean = false;
  isChatRoom: Boolean = true;
  chat_room: String = '';
  chat_room_name: String = '';
  chat_id = null;
  delThread = null;

  deleteThreadConfirmModalRef: NgbModalRef;
  deleteThreadSuccessModalRef: NgbModalRef;

  roomForm = new FormGroup({
    roomName: new FormControl(''),
  });

  constructor(
    private router: Router,
    private modal: NgbModal, 
    private chatService: ChatService,
  ) { }

  ngOnInit(): void {
    this.chatService.getUser().subscribe((res) => {
      if(res.length !== 0) {
        this.authUser = res;
      }
    })

    this.chatService.getSubUser().subscribe((res) => {
      if(res.length !== 0) {
        this.authUser = res;
      }
    })

    this.chatService.getOrg().subscribe((res) => {
      this.organization = res;
    })

    this.chatService.getUsers().subscribe((res) => {
      Object(res).forEach(user => {
        this.users.push({
          'id': user.userId, 
          'firstName': user.firstName, 
          'lastName': user.lastName, 
          'email': user.email,
          'contactNo': user.contactNo,
          'profilepic': user.profilepic,
          'lastLogin': user.lastLogin,
          'activityLog': user.activityLog,
          'status': user.status,
          'createdDateTime': user.createdDateTime,
          'updatedDateTime': user.updatedDateTime
        })
      })
    })

    this.chatService.getSubUsers().subscribe((res) => {
      Object(res).forEach(user => {
        this.users.push({
          'id': user.subUserId, 
          'firstName': user.firstName, 
          'lastName': user.lastName, 
          'email': user.email,
          'contactNo': user.contactNo,
          'profilepic': user.profilepic,
          'lastLogin': user.lastLogin,
          'activityLog': user.activityLog,
          'status': user.status,
          'createdDateTime': user.createdDateTime,
          'updatedDateTime': user.updatedDateTime
        })
      })
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
    this.roomForm.reset();
    this.createRoom = false;
  }

  selectChatRoom(room_name) {
    this.chat_room = room_name;
  }

  deleteChatRoom(template, id) {
    this.chatService.deleteChatRoom(id).subscribe(res => {
      this.rooms = this.rooms.filter(room => room.id !== id);
      var chat = this.rooms.slice(-1)[0];
      this.chat_room = chat.name;
      this.chat_room_name = chat.temp_name;
      this.closeDeleteModal()
      this.deleteThreadSuccess(template)
    }, error => {
      console.log(error)
    })
  }

  getRoomMessage(message: any) {
    
    message.forEach(msg => {
      this.roomMessage = msg;
    })

    if(this.roomMessage.length !== 0) {
      if(!this.rooms.some((r) => r.id == this.roomMessage['thread_id'])) {
        this.rooms.push({id: this.roomMessage['thread_id'], name: this.roomMessage['thread'], date_created: this.roomMessage['date_created'], is_archived: false, temp_name: this.roomMessage['thread']})
      }
    }
  }

  deleteThread(template, id) {
    this.delThread = id;
    this.deleteThreadConfirmModalRef = this.modal.open(template, { backdrop: true, size: 'sm', centered: true })
  }

  deleteThreadSuccess(template) {
    this.deleteThreadSuccessModalRef = this.modal.open(template, { backdrop: true, size: 'sm', centered: true })
  }

  closeDeleteModal() {
    this.deleteThreadConfirmModalRef.close()
  }

  closeDeleteSuccessModal() {
    this.deleteThreadSuccessModalRef.close()
  }
}
