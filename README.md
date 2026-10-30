# 017 Title Updater

Rewrites the video title every 10 minutes: "{views} people know I'm quitting my job in {days} days", counting down to 7 May 2027 (Melbourne time).

## 1. Google Cloud (one-off)
1. console.cloud.google.com > new project > APIs & Services > Library > enable **YouTube Data API v3**.
2. OAuth consent screen > External > fill the basics > add your Google account as a test user.
3. **Publish the app ("In production").** Left in Testing, the login dies after 7 days and the title stops updating.
4. Credentials > Create credentials > OAuth client ID > **Desktop app** > download the JSON into this folder.

## 2. Sign in (one-off)
    python3 login.py
Pick the channel's Google account. Google warns "unverified app": Advanced > Go to (your app). It's your own app.
This saves `token.json` and prints three secrets.

## 3. Test on an unlisted video
    python3 update_title.py --test
    python3 update_title.py TEST_VIDEO_ID --dry-run
    python3 update_title.py TEST_VIDEO_ID
Check the title changed and the description is still there.

## 4. Run it every 10 minutes on GitHub
1. Make a **public** GitHub repo (private repos run out of free minutes at this rate) and push this folder to it. `.gitignore` keeps your secrets file and token out.
2. Repo > Settings > Secrets and variables > Actions:
   - Secrets: `CLIENT_ID`, `CLIENT_SECRET`, `REFRESH_TOKEN` (from step 2)
   - Variables: `VIDEO_ID` (the real video's ID)
3. Actions tab > Update video title > **Run workflow** once to check it works.

Uses at most about 7,344 of the daily 10,000 API units (144 checks, plus 50 per title change). A monthly empty "Keepalive" commit stops GitHub switching the schedule off.

## 5. Reliable 10-minute timer (cron-job.org)
GitHub's own schedule skips most runs, so cron-job.org starts the workflow every 10 minutes instead:
- POST `https://api.github.com/repos/XxDisfiguredSpacexX/countdown-title/actions/workflows/update-title.yml/dispatches`, body `{"ref":"main"}`
- Headers: `Authorization: Bearer <fine-grained token, Actions read/write on this repo only>`, `Accept: application/vnd.github+json`, `X-GitHub-Api-Version: 2022-11-28`, `Content-Type: application/json`
- A good response is 204. The token expires 1 June 2027.
GitHub's own hourly schedule stays on as a backup.
