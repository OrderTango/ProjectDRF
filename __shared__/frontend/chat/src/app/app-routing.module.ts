import { NgModule } from '@angular/core';
import { Routes, RouterModule } from '@angular/router';
import { ChatComponent } from './components/chat/chat.component';
import { ChatRoomComponent } from './components/chat-room/chat-room.component';
import { HomeComponent } from './components/home/home.component';


const routes: Routes = [
  { path: '', redirectTo: 'chat', pathMatch: 'full'},
  { path: 'home', component: HomeComponent },
  { path: 'chat', component: ChatComponent },
  { path: 'chat/:room_name', component: ChatRoomComponent },
];

@NgModule({
  imports: [RouterModule.forRoot(routes)],
  exports: [RouterModule]
})
export class AppRoutingModule { }
