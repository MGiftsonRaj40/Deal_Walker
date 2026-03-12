# 🚀 DealWalker – Real-Time Online Auction Platform

![Python](https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white)
![Flask](https://img.shields.io/badge/Flask-000000?style=for-the-badge&logo=flask)
![MongoDB](https://img.shields.io/badge/MongoDB-4EA94B?style=for-the-badge&logo=mongodb&logoColor=white)
![Socket.IO](https://img.shields.io/badge/Socket.IO-black?style=for-the-badge&logo=socket.io)
![JavaScript](https://img.shields.io/badge/JavaScript-F7DF1E?style=for-the-badge&logo=javascript&logoColor=black)
![HTML](https://img.shields.io/badge/HTML-E34F26?style=for-the-badge&logo=html5&logoColor=white)
![CSS](https://img.shields.io/badge/CSS-1572B6?style=for-the-badge&logo=css3&logoColor=white)
![MongoDB Atlas](https://img.shields.io/badge/MongoDB%20Atlas-13AA52?style=for-the-badge&logo=mongodb)

---

## 📌 Project Overview

**DealWalker** is a **real-time online auction platform** that enables users to create and participate in auctions through an interactive web interface.

The system supports **two user roles:**

- 🧑‍💼 **Auctioneer** – Creates and manages auctions  
- 🧑‍💻 **Bidder** – Participates in auctions by placing bids  

The platform uses **Flask + MongoDB + WebSockets (Socket.IO)** to provide **instant bid updates and live auction interactions**.

It also integrates **email verification, password recovery, real-time notifications, and automated auction scheduling**.

---

## 🖥️ Application Screenshots

### 🔐 Login & Authentication
![DealWalker Login](images/4.png)

### 📦 Post Auction Item
![DealWalker Post Auction](images/2.png)

### 🏠 Auction Home Page
![DealWalker Home](images/1.png)

### ⚡ Live Bidding Interface
![DealWalker Bidding](images/3.png)

---

## 🎯 Key Features

### 🔐 User Authentication
- Secure **Sign Up & Sign In**
- **Email verification using OTP**
- **Password hashing using Flask-Bcrypt**
- **Password reset via secure email token**
- Session management using **Flask-Login**

---

### 👥 Role-Based Access Control

The system provides separate dashboards for each role.

#### 🧑‍💼 Auctioneer
- Create and post auction items
- Upload product images
- Set initial auction price
- Monitor live bids
- Manually close auctions
- Delete auction listings
- Track auction success statistics

#### 🧑‍💻 Bidder
- Browse all active auctions
- Place bids in real time
- View current highest bid
- Track auctions participated in
- Track auctions won

---

### ⚡ Real-Time Bidding System

Implemented using **Flask-SocketIO** for live communication.

Features include:

- Instant bid updates across all clients
- Real-time highest bidder tracking
- Live auction status updates
- Automatic auction close notifications

---

### ⏱️ Automated Auction Management

- Automatic auction closing using **APScheduler**
- Manual auction termination by auctioneer
- Automatic deletion of completed auctions
- Periodic background cleanup of expired auctions

---

### 🖼️ Image Storage & Processing

Auction images are handled efficiently using:

- **MongoDB GridFS** for storing large files
- **Pillow (PIL)** for image resizing
- Optimized image delivery with caching

---

### 📧 Email Services

The platform integrates **Flask-Mail** for communication.

Supported email features:

- Account verification during signup
- Password reset email links
- Secure email-based authentication flows

---

### 👤 User Profile Management

Users can personalize their profiles with:

- Avatar uploads
- Profile statistics
- Auction performance tracking

---

## 🧰 Technology Stack

### 🔹 Backend
- Python
- Flask
- Flask-Login
- Flask-SocketIO
- Flask-Bcrypt
- Flask-Mail

### 🔹 Database
- MongoDB Atlas
- GridFS (for file storage)

### 🔹 Real-Time Communication
- Socket.IO
- Eventlet

### 🔹 Task Scheduling
- APScheduler

### 🔹 Image Processing
- Pillow (PIL)

### 🔹 Frontend
- HTML5
- CSS3
- JavaScript

---

## 📂 Project Structure
