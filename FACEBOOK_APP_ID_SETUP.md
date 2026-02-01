# How to Get Your Facebook App ID for Cheshire Today

## Why You Need a Facebook App ID

The `fb:app_id` meta tag allows Facebook to:
- Track how your content is shared
- Provide better analytics (insights)
- Show proper attribution when shared
- Enable Facebook Comments plugin (if you add it later)

**Note:** It's technically optional, but highly recommended for better Facebook integration.

---

## Step-by-Step: Create a Facebook App

### Step 1: Go to Facebook Developers
1. Visit: https://developers.facebook.com/
2. Click **My Apps** in the top right
3. Click **Create App**

### Step 2: Choose App Type
1. Select **Business** (or **Consumer** if you prefer)
2. Click **Next**

### Step 3: Fill in App Details
- **App Name**: `Cheshire Today`
- **App Contact Email**: Your email address
- **Business Account**: Select your business account (or skip if you don't have one)
- Click **Create App**

### Step 4: Complete Security Check
- Complete the CAPTCHA
- Click **Submit**

### Step 5: Get Your App ID
1. You'll see your **App ID** on the dashboard
2. It looks like a number: `1234567890123456`
3. Copy this number

### Step 6: Add Facebook Login (Optional but Recommended)
1. In the dashboard, find **Facebook Login**
2. Click **Set Up**
3. Select **Web**
4. Enter your website URL: `https://cheshiretoday.co.uk`
5. Click **Save**
6. Go to Settings → Basic
7. Add your **App Domains**: `cheshiretoday.co.uk`
8. **Privacy Policy URL**: `https://cheshiretoday.co.uk/privacy` (you'll need to create this)
9. Click **Save Changes**

### Step 7: Make App Live (Important!)
1. In the top right of the dashboard, you'll see a toggle that says **Development**
2. Click it to switch to **Live** mode
3. Confirm the change

---

## Update Your Website with the App ID

### Option 1: I'll Do It For You (Tell Me Your App ID)

Just share your Facebook App ID with me, and I'll update the file for you!

### Option 2: Update It Yourself

1. Open the file: `/app/frontend/public/index.html`
2. Find the line: `<meta property="fb:app_id" content="YOUR_FACEBOOK_APP_ID" />`
3. Replace `YOUR_FACEBOOK_APP_ID` with your actual App ID
4. Save the file
5. Restart the frontend:
   ```bash
   sudo supervisorctl restart frontend
   ```

---

## Quick Alternative: Skip the App ID (Not Recommended)

If you want to skip this for now and just test sharing:

1. The App ID is technically optional
2. Facebook will still show your content when shared
3. You just won't get detailed analytics
4. You can add it later when you have time

---

## Verify It's Working

After adding your App ID:

1. Go to: https://developers.facebook.com/tools/debug/
2. Enter: `https://cheshiretoday.co.uk/`
3. Click **Debug**
4. Check that:
   - ✓ No `fb:app_id` error
   - ✓ Image shows correctly
   - ✓ Title and description are correct
5. If cached, click **Scrape Again**

---

## What Your App ID Looks Like

Example format: `123456789012345`
- It's a 15-16 digit number
- You'll find it in your Facebook Developers dashboard
- Keep it safe, but it's not secret (it's visible in your HTML)

---

## Benefits of Having an App ID

### With App ID:
✓ See which articles are most shared
✓ Track social traffic in Facebook Analytics
✓ Enable Facebook Comments on articles (optional)
✓ Better control over how content appears
✓ Professional setup

### Without App ID:
✓ Content still shares fine
✗ No detailed analytics
✗ Can't use advanced Facebook features
✗ Facebook debugger shows warning

---

## Need Help?

**Can't create the app?**
- Make sure you're logged into Facebook with admin access
- Verify your Facebook account is verified (phone/email)
- If stuck, you can temporarily skip this and add it later

**Getting errors?**
- Make sure App is set to "Live" mode (not "Development")
- Check that App Domains includes: `cheshiretoday.co.uk`
- Verify your website URL is correct

---

## Current Status

Your website currently has a placeholder:
```html
<meta property="fb:app_id" content="YOUR_FACEBOOK_APP_ID" />
```

**To fix:**
1. Create Facebook App (5 minutes)
2. Get your App ID
3. Share it with me OR update the file yourself
4. Restart frontend
5. Test in Facebook Debugger

---

## Timeline

- **Creating App**: 5-10 minutes
- **Updating Website**: 1 minute
- **Testing**: 2 minutes
- **Total**: About 15 minutes

Let me know your App ID when you have it, and I'll update it for you! 🎉
