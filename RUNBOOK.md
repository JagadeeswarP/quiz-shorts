# Failure Mode quiz Shorts: automation runbook

Channel: **Failure Mode** (YouTube channel id `UC9U7y4PCC8KduDnkxTztfvQ`), posted through the Zapier connector
(app `YouTubeV4CLIAPI`, action `upload_video`, tool `youtube_upload_video`).
Repo: `JagadeeswarP/quiz-shorts` (public, used only as a temporary file host plus this code).

## Files
- `quiz.py`: renderer. `python3 quiz.py quizzes/<name>.json v/<name>.mp4` makes a 27 s 1080x1920 Short (needs numpy, Pillow, ffmpeg, Poppins-Bold and NotoColorEmoji fonts). `python3 quiz.py quizzes/<name>.json /tmp/<name> 0.8,6.4` saves still frames for checking.
- `quizzes/*.json`: one quiz each: title, hook1, hook2, hook_emoji, bg colours, `style` (pattern dots|stripes|waves, timer ring|ring-left|bar, bpm, root note Hz), 5 questions (emoji and/or text, 3 options, answer index, short fact) and `yt` (title, description, tags).
- `queue.json`: `queue` = names still to post, in order. `posted` = log of {name, video_id, posted_at_ist, slot}.

## Upload run (each posting slot)
1. Clone the repo (depth 1). If the queue is empty, notify the user and stop.
2. Take the first name in `queue`. Render it to `v/<name>.mp4`. Render 2 stills and look at them: nothing cut off, emoji visible, answer highlighted.
3. Commit and push `v/<name>.mp4`. Check `https://raw.githubusercontent.com/JagadeeswarP/quiz-shorts/main/v/<name>.mp4` returns HTTP 200.
4. Inspect then execute the Zapier action `upload_video` with: video = that raw URL, title/description/tags from `yt`, privacy_status `public`, category_id `27`, made_for_kids `false`, notify_subscribers `true`, default_language `en`, license `youtube`, embeddable `true`.
5. Delete `v/<name>.mp4`, move the name from `queue` to `posted` with the returned video id, IST time and slot hour. Commit and push.
6. Notify the user with the video link. If any step fails, retry once, then notify the user with the error and stop (never post twice).

## Weekly run (Sunday evening)
1. Views: for every posted video at least 48 h old, get its view count (Zapier YouTube actions; inspect first) and the channel's subscriber count. Save a summary to `stats.md`.
2. Timing: once 7+ days of posts exist, compare average views per slot hour. If a slot averages under 60% of the best slot, move it by 1 to 3 hours toward the better-performing times. Keep 3 posts a day at least 4 hours apart. Update the upload scheduled task's cron (in Asia/Kolkata) and record the change in `stats.md`.
3. Refill: write new quizzes so `queue` holds at least 21. Follow the content rules below. Commit, push and notify the user with a short summary (views, subscribers, best format, any time change).

## Content rules (monetisation safe)
- Original questions only; never copy other quiz channels. Rotate formats: flags, emoji (movies, food, animals, songs as titles only), science, space, human body, geography/capitals, true-or-false, odd one out, "which is bigger/older".
- Every answer must be correct and checkable; skip disputed or fast-changing facts. One short true fact per answer.
- No misleading claims: no "only 1% know", "99% fail", invented stats or "impossible". Honest hooks such as "Can you get all 5?".
- No logos, posters, screenshots, characters, song lyrics or outside music. Emoji, plain text and synthesised sound only.
- Vary `style` and `bg` between consecutive quizzes. Keep text short, timer 3 s, length about 27 s.
- Not made for kids; nothing violent, adult or political.
