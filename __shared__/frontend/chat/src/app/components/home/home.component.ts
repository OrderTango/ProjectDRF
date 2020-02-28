import { Component, OnInit } from '@angular/core';
import { ChatService } from '../../services/chat.service';

@Component({
  selector: 'app-home',
  templateUrl: './home.component.html',
  styleUrls: ['./home.component.sass']
})
export class HomeComponent implements OnInit {

  users = [];

  constructor(
    private chatService: ChatService,
  ) { }

  ngOnInit(): void {
    
    this.chatService.getUsers().subscribe((res) => {
      console.log(res)
      this.users = Object(res);
    })
  }

}
