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
  @Input() member_fn: string;
  @Input() member_ln: string;
  @Output() roomMessage = new EventEmitter<any>();

  messageForm = new FormGroup({
    content: new FormControl(''),
    messageContent: new FormControl(''),
  })

  private chatSocket;
  private chatUser: string;
  private socketMessages = [];
  isAuthUser: boolean;
  thisUser = null;
  messageId = null;
  hasChatRoom: boolean = false;
  hasMessages: boolean = false;
  isAuthSender: boolean = false;
  messages = [];
  msg = [];
  users = [];
  subUsers = [];
  addedMembers = [];
  roomMembers = [];
  roomNewName: String = '';

  addMemberModalRef: NgbModalRef;
  deleteMessageModalRef: NgbModalRef;
  deleteMessageSuccessModalRef: NgbModalRef;

  constructor(
    private activatedRoute: ActivatedRoute,
    private router: Router,
    private modal: NgbModal,
    private chatService: ChatService,
  ) { }

  ngOnInit(): void {
    
    this.chatService.getUser().subscribe((res) => {
      this.chatUser = res.userId;

      this.thisUser = {
        'id': res.userId, 
        'firstName': res.firstName, 
        'lastName': res.lastName, 
        'email': res.email,
        'contactNo': res.contactNo,
        'profilepic': res.profilepic,
        'lastLogin': res.lastLogin,
        'activityLog': res.activityLog,
        'status': res.status,
        'createdDateTime': res.createdDateTime,
        'updatedDateTime': res.updatedDateTime
      }
    }, error => {
      console.log(error)
    })

    this.chatService.getSubUser().subscribe((res) => {
      this.chatUser = res.subUserId

      this.thisUser = {
        'id': res.subUserId, 
        'firstName': res.firstName, 
        'lastName': res.lastName, 
        'email': res.email,
        'contactNo': res.contactNo,
        'profilepic': res.profilepic,
        'lastLogin': res.lastLogin,
        'activityLog': res.activityLog,
        'status': res.status,
        'createdDateTime': res.createdDateTime,
        'updatedDateTime': res.updatedDateTime
      }
      console.log('THIS USER: ', this.thisUser)
    }, error => {
      console.log(error)
    })

    this.chatService.getSubUsers().subscribe((res) => {
      this.subUsers = Object(res)
    }, error => {
      console.log(error)
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
    }, error => {
      console.log(error)
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
    }, error => {
      console.log(error)
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
    console.log('ROOM: ', room_name)
    if(room_name === '' || room_name === undefined) {
      this.hasChatRoom = false;
    }else {
      console.log('JOJAS')
      this.hasChatRoom = true;
      this.createWebSocket(room_name);
    }
  }

  createWebSocket(room_name) {

    let baseurl = window.location.origin.replace(/^http(s?):\/\//i, "");

    this.chatSocket = new ReconnectingWebSocket (
      `ws://${baseurl}/ws/api-chat/${room_name}/`,
    )
    console.log(this.chatSocket)

    this.chatSocket.debug = true;

    this.chatSocket.onopen = (e) => {
      console.log('HERE OnOPEN')
      this.fetchMessages();
    }

    this.chatSocket.onmessage = (e) => {
      var data = JSON.parse(e.data);
      let command = data['command']; 

      console.log('DATA: ', data)

      if(command === 'fetch_message') {
        this.messages = data['message']
        this.msg.push({'thread_id': data['thread_id'], 'thread': data['thread']})
        this.roomMessage.emit(this.msg)

        if(this.messages.length !== 0) {
          var message = []
          var sender = []
          message = this.messages[0];

          this.messages.forEach(m => {
            console.log(m)
            m['isAuthUser'] = '';
            
            if("user_sender" in m) {
              console.log(m.user_sender, this.thisUser.email)
              if(m.user_sender === this.thisUser.email) {
                // this.messages.forEach(item => item['isAuthUser'] = true);
                m.isAuthUser = true;
              }else{
                // this.messages.forEach(item => item['isAuthUser'] = false);
                m.isAuthUser = false;
              }
            }else if("subuser_sender" in m) {
              console.log(m.subuser_sender, this.thisUser.email)
              if(m.subuser_sender === this.thisUser.email) {
                // this.messages.forEach(item => item['isAuthUser'] = true);
                m.isAuthUser = true;
              }else{
                // this.messages.forEach(item => item['isAuthUser'] = false);
                m.isAuthUser = false;
              }
            }
          })

          console.log(this.messages)

          if(message['members'].length === 0) {
            this.roomMembers = [];
          }

          message['members'].forEach(m => {
            let member_name = '';
            let member_id = null;

            if("user_member" in m) {
              member_name = m.user_member;
              member_id = m.user_member_id;
            }else if("subuser_member") {
              member_name = m.subuser_member;
              member_id = m.subuser_member_id;
            }
            
            if(member_id !== null) {
              if(member_id !== undefined) {
                if(!this.roomMembers.some((rm) => rm.member_id == member_id)) {
                  this.roomMembers.push({
                    'thread': m.thread,
                    'member_id': member_id,
                    'member': member_name,
                    'date_added': m.date_added
                  })
                }
              }
            }
          })

          if(message['message'] === null) {
            this.hasMessages = false;
          }else{
            this.hasMessages = true;
          }

        }else{
          this.hasMessages = false;
        }
      }else {
        var msg = data['message']
        
        if(!this.messages.some((m) =>  msg['message_id'] == m['message_id'])) {
          this.messages.push(data['message']); 
        }

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
    console.log('HERE 2 ', this.chatSocket.send(JSON.stringify({'from': this.thisUser, 'command': 'fetch_message'})))
    this.chatSocket.send(JSON.stringify({
      'from': this.thisUser,
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
    console.log('HERE 3')
    if(message !== '') {
      this.chatSocket.send(JSON.stringify({
        'message': message,
        'command': 'new_message',
        'from': this.thisUser
      }));
  
      this.messageForm.reset();
    }
  }

  deleteMessage(template, id) {
    this.messageId = id;
    this.deleteMessageModalRef = this.modal.open(template, { backdrop: true, size: 'sm', centered: true })
  }

  deleteUserMessage(template) {
    // this.chatSocket.send(JSON.stringify({
    //   'thread': this.room_name,
    //   'command': 'delete_message',
    //   'message_id': this.messageId
    // }))

    // this.messages = this.messages.filter(m => m.message_id !== this.messageId)
    this.closeDeleteModal();
    setTimeout(() => {
      this.deleteMessageSuccess(template)
    }, 3000);
  }

  deleteMessageSuccess(template) {
    this.deleteMessageSuccessModalRef = this.modal.open(template, { backdrop: true, size: 'sm', centered: true })
  }

  closeDeleteModal() {
    this.deleteMessageModalRef.close()
  }

  closeDeleteSuccessModal() {
    this.deleteMessageSuccessModalRef.close()
  }

  addMemberModal(template) {
    this.addMemberModalRef = this.modal.open(template, { backdrop: true, size: 'lg', centered: true })
  } 

  closeMemberModal() {
    this.addMemberModalRef.close()
  }

  selectedMember(user) {
    if(user.id !== this.chatUser) {
      if(!this.addedMembers.some((m) => m.id == user.id)) {
        this.addedMembers.push({'id': user.id, 'firstName': user.firstName, 'lastName': user.lastName, 'email': user.email})
      }
    }
  }

  addMember() {
    console.log('here 2323')
    if(this.addedMembers.length !== 0) {
      this.chatSocket.send(JSON.stringify({
        'thread': this.room_name,
        'command': 'new_member',
        'members': this.addedMembers
      }))
    }
  }

  removeAddedMember(id) {
    this.addedMembers = this.addedMembers.filter(room => room.id !== id);
  }

  removeMember(room, id) {
    this.chatService.removeRoomMember(room, id).subscribe(res => {
      if(this.thisUser.id !== id) {
        this.roomMembers = this.roomMembers.filter(member => member.member_id !== id);
      }
    }, error => {
      console.log(error)
    })
  }

}
