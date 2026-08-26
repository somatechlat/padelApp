# 🚀 PadelApp Testing Guide

## ✅ What's Ready to Test

**All Systems Running:**
- ✅ PostgreSQL Database (port 5432)
- ✅ Redis Cache (port 6379)
- ✅ Django Backend API (port 8000)
- ✅ Celery Worker (async tasks)
- ✅ Flutter APK Built & Ready

**APK Location:** `./padelapp-debug.apk` (86 MB)

**Full build & deploy instructions:** [docs/BUILD_AND_DEPLOY.md](docs/BUILD_AND_DEPLOY.md)

---

## 📱 Installation on Physical Phone

### Option 1: Via ADB (USB or Wireless Debugging)

```bash
# If phone is connected via USB with debugging enabled
adb install ./padelapp-debug.apk

# OR for wireless debugging (phone & computer on same WiFi)
adb connect 192.168.100.XXX:5555  # Replace XXX with phone IP
adb install ./padelapp-debug.apk
```

### Option 2: Manual Installation
1. Copy `padelapp-debug.apk` to your phone (USB, email, cloud storage)
2. On phone: Open file manager → locate APK → tap to install
3. Confirm permissions and install

---

## 🔑 Test Accounts

### Mobile App Login

```
Email:    cliente@andespadel.com
Password: Andes12345!
Role:     cliente
```

### Admin Panel Access

```
URL:      https://andespadel.yachaq.io/adminpanel/login/
Email:    admin@andespadel.com
Password: Andes12345!
```

---

## ✨ What to Test

### Mobile App

1. **Authentication**
   - Login with above credentials
   - Check dashboard loads
   - View existing bookings
   - Check notifications

2. **Bookings**
   - View available courts
   - Check court availability
   - Make a new booking

3. **User Profile**
   - View profile information
   - Edit language preferences (Spanish, English, Catalan, Portuguese)
   - Change password

4. **Events & Tournaments**
   - Browse events
   - View tournament details
   - Check event calendar

### Admin Dashboard

1. **Dashboard**
   - View bookings for today
   - Check court occupancy
   - Monitor revenue
   - Review alerts

2. **Courts Management**
   - View all courts
   - Check scheduling
   - Manage maintenance windows

3. **Users**
   - View all users
   - Check roles and status
   - Edit user details

4. **Bookings Management**
   - View all bookings
   - Apply cancellation policies
   - Track no-show penalties

5. **Reports**
   - Generate revenue reports
   - Check occupancy reports
   - Review audit logs

---

## 🌐 Network Details

**Production Server:** `https://andespadel.yachaq.io`

**Services Available:**

| Service | URL | Port |
|---------|-----|------|
| Backend API | https://andespadel.yachaq.io/api | 443 |
| Admin Panel | https://andespadel.yachaq.io/adminpanel | 443 |
| Landing Page | https://andespadel.yachaq.io | 443 |

**Local Development (Docker):**

| Service | URL | Port |
|---------|-----|------|
| Backend API | http://localhost:8000/api | 8000 |
| Admin Panel | http://localhost:8000/adminpanel | 8000 |
| Database | localhost:5432 | 5432 |
| Redis | localhost:6379 | 6379 |

---

## 🛠️ Useful Commands

### View Backend Logs
```bash
cd /Users/macbookpro201916i964gb1tb/Documents/GitHub/padelApp
make logs
```

### Database Shell
```bash
make psql
```

### Django Shell
```bash
make shell
```

### Run Tests
```bash
make test
```

### Lint Code
```bash
make lint
```

### Rebuild Services
```bash
make down
make build
make up
make migrate
make seeddemo
```

---

## 🎯 Demo Data Loaded

**Sample Data:**
- ✅ Courts created
- ✅ Time slots configured
- ✅ Sample bookings created (3 test reservations)
- ✅ Notification emails simulated

**Login:** All demo users have password: `Andes12345!`

---

## 🚨 Troubleshooting

### APK Won't Install
- Ensure `Unknown Sources` is enabled in phone settings
- Check Android version (min SDK 24, target 34)
- Try clearing app cache first: `adb shell pm clear com.andes.padel.padel_app`

### Can't Connect to Backend
- Verify phone has internet access
- Test: Open browser on phone → `https://andespadel.yachaq.io/api/auth/me/`
- Should see: `{"detail":"Las credenciales de autenticación no se proveyeron."}`

### Bookings Not Loading
- Check backend logs: `make logs`
- Verify database is healthy: `make psql` then `SELECT count(*) FROM bookings_booking;`

### Login Issues
- Clear app cache: `adb shell pm clear com.andes.padel.padel_app`
- Force stop app and restart
- Check storage permissions on phone

---

## 📊 Dashboard Features

**Real-Time Metrics:**
- Bookings today count
- Court occupancy percentage
- Revenue tracking
- System alerts
- Pending actions

**Admin Actions:**
- Manage courts & schedules
- Process payments
- Handle cancellations
- Generate reports
- View audit logs

---

## ✅ Checklist Before Presentation

- [ ] APK installed on phone
- [ ] Phone has internet access (connects to andespadel.yachaq.io)
- [ ] Backend running (check https://andespadel.yachaq.io/api/auth/me/)
- [ ] Can login to mobile app
- [ ] Can access admin dashboard (https://andespadel.yachaq.io/adminpanel)
- [ ] Can view bookings on mobile
- [ ] Can see demo data in admin panel
- [ ] Test booking creation workflow

---

## 🔗 API Endpoints Ready

**Public (No Auth):**
- POST `/api/auth/login/`
- POST `/api/auth/register/`
- POST `/api/auth/verify/`
- POST `/api/auth/password-reset/`

**Protected (JWT Auth):**
- GET `/api/auth/me/`
- GET `/api/bookings/`
- GET `/api/courts/`
- GET `/api/tournaments/`
- GET `/api/notifications/`
- POST `/api/bookings/` (create booking)
- POST `/api/payments/` (process payment)

---

**🎉 Ready to Test! Happy Coding!**
