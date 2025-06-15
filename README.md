# Sales CRM System

A comprehensive Sales CRM system with role-based access control, coin rewards, and shop management.

## Features

- **Multi-role Authentication**: Super Admin, Admin, Agent
- **Sales to Coins Conversion**: Automated reward system
- **Shop Management**: Prize creation, redemption, reward bag
- **User Management**: Complete credential management
- **Target System**: Monthly performance tracking
- **Leaderboard**: Agent ranking system

## Tech Stack

- **Backend**: FastAPI + Python
- **Frontend**: React + Tailwind CSS
- **Database**: MongoDB Atlas
- **Authentication**: JWT tokens

## Super Admin Login

- **Username**: tharme.ritta
- **Password**: Tharme@789

## System Overview

### User Roles
- **Super Admin**: Complete system control
- **Admin**: Manage agents and approve requests
- **Agent**: Submit sales, redeem rewards

### Sales to Coins
- $100 = 0.5 coins + 1 deposit
- $250 = 1 coin + 1.5 deposits  
- $500 = 3 coins + 3 deposits

### Workflow
1. Agent submits coin request for sale
2. Admin/Super Admin approves
3. Coins automatically added to agent
4. Agent can redeem prizes from shop
5. Admin approves reward usage

## License

MIT License
