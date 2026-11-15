# Failure Mode quiz Shorts: automation runbook

Channel: **Failure Mode** (YouTube channel id `UC9U7y4PCC8KduDnkxTztfvQ`), posted through the Zapier connector
(app `YouTubeV4CLIAPI`, action `upload_video`, tool `youtube_upload_video`).
Repo: `JagadeeswarP/quiz-shorts` (public, used only as a temporary file host plus this code).

## Files
- `quiz.py`: renderer v2. `python3 quiz.py quizzes/<name>.json v/<name>.mp4` makes a narrated 1080x1920 Short of about 30–45 s (needs numpy, Pillow, ffmpeg, Poppins-Bold and NotoColorEmoji fonts). `python3 quiz.py quizzes/<name>.json /tmp/<name> 1.0,7.0` saves still frames (layout check, no audio).
- `tts.py`: Kokoro-82M narration (Apache-2.0, runs locally). Installs `kokoro-onnx` and downloads its model from GitHub on first use (~340 MB, about a minute). Voice `af_heart` (smooth, not deep). Never use Qwen TTS.
- Landscape long-video mode (weekly challenge): add `"format": "landscape"`, `"think": 10`, `"speak_fact": true`, `"outro_text": "New challenge every Sunday!"` and an `outro_say` to the quiz JSON. quiz.py then renders 1920x1080 (question card left, options right, timer strip, fact pill below), gives a 10 s timer and reads each fact aloud after the answer. Stills work the same way.
- Layouts per question: `mcq` (3 stacked options, emoji/text clue), `versus` (2 side-by-side choices with `opt_emoji`: true/false, which is bigger/taller/faster/older), `tiles` (4 emoji tiles: odd one out). Spoken question = `say`, else the question `text`, else the quiz-level `ask`. Spoken answer = `say_answer` (keep it short), else "<answer>!". Any number of questions works (5 for normal Shorts, 20 for the weekly challenge).
- `quizzes/*.json`: one quiz each: title, hook1, hook2, hook_emoji, bg colours, `style` (pattern dots|stripes|waves, timer ring|ring-left|bar, bpm, root note Hz), 5 questions (emoji and/or text, 3 options, answer index, short fact) and `yt` (title, description, tags).
- `plan.csv`: THE 20-day content plan (from the user's Excel plan). Columns: id, date, slot_ist, format, layout, topic, title, hook, questions, file, status (planned|written|posted|skipped), video_id, views. Posting follows this file in id order.
- `queue.json`: legacy queue plus the `posted` log of {name, video_id, posted_at_ist, slot}. Keep appending to `posted`.

## Format codes in plan.csv
- DUEL: "Do You Know More About X or Y?" 6 mcq questions alternating the two topics; put the topic in caps on the first line of `text` ("GEOGRAPHY\n…") and in `say` ("Geography. …").
- TF: true or false, 5 `versus` questions with options [True, False] and opt_emoji [✅, ❌]; mix true and false answers.
- ONE: a single question (8–15 s Short). Hook "One question:" / "3 seconds. Go!". mcq or versus.
- GRADE: "Are You Smarter Than a 5th Grader?" 5 school-level mcq questions on the row's subject, getting harder.
- FOOT: football (soccer) quiz, 5 mcq; only long-settled facts (past tournament results, rules, records), nothing about current seasons or transfers.
- GEO, SCI, ANIM, EMOJI: 5 mcq on the row's topic. VS: 5 `versus` head-to-head comparisons with opt_emoji. ODD: 5 `tiles` odd-one-out rounds with 4 opt_emoji each.
- CHAL: the Sunday 20-question challenge, posted by the weekly run as a **landscape long video (not a Short)**, about 5–7 minutes.

## Upload run (each posting slot)
1. Clone the repo (depth 1). Open plan.csv and take the first row (lowest id) whose status is `planned` or `written` and whose format is not CHAL. If none is left, notify the user and stop.
2. If its `file` is empty or the JSON doesn't exist, write `quizzes/<slug>.json` for that row now: use the row's topic, title (as yt.title), hook and question count, follow the format codes above and the content rules below, fact-check every answer, and write a unique description. Set `file`. Render it to `v/<file>.mp4`. Render 2 stills and look at them: nothing cut off, emoji visible, answer highlighted.
3. Commit and push `v/<name>.mp4`. Check `https://raw.githubusercontent.com/JagadeeswarP/quiz-shorts/main/v/<name>.mp4` returns HTTP 200.
4. Inspect then execute the Zapier action `upload_video` with: video = that raw URL, title/description/tags from `yt`, privacy_status `public`, category_id `27`, made_for_kids `false`, notify_subscribers `true`, default_language `en`, license `youtube`, embeddable `true`.
5. Delete the mp4. In plan.csv set that row's status to `posted` and video_id. Append {name, video_id, posted_at_ist, slot} to queue.json `posted` (and remove the name from `queue` if present). Commit and push.
6. Notify the user with the video link. If any step fails, retry once, then notify the user with the error and stop (never post twice).

## Weekly run (Sunday evening)
1. Views: for every posted video at least 48 h old, get its view count (Zapier YouTube actions; inspect first) and the channel's subscriber count. Write views into plan.csv `views` and a summary (by format and by slot) to `stats.md`.
2. Timing: once 7+ days of posts exist, compare average views per slot hour. If a slot averages under 60% of the best slot, move it by 1 to 3 hours toward the better-performing times. Keep 3 posts a day at least 4 hours apart. Update the upload scheduled task's cron (in Asia/Kolkata) and record the change in `stats.md`.
3. Plan upkeep: pre-write the quiz JSON for the next 7 days of plan.csv rows (status `written`). If a format is clearly underperforming (under half the average views after 3+ posts), replace its upcoming rows with the best format and note it in stats.md. When fewer than 7 days of rows remain, append 7 more days in the same 3-slot pattern. (Old refill rule:  Follow the content rules below. Mix layouts across the week.)
4. Weekly challenge (long video, from 2026-11-22 on): write one new 20-question quiz (`challenge-YYYY-MM-DD.json`, title like "20-QUESTION CHALLENGE", questions not used in any earlier quiz, all four levels) with the landscape keys above (`format` landscape, `think` 10, `speak_fact` true, outro). Render it in landscape: it should run about 5–7 minutes (if it comes out under 5, raise `think` to 12; over 7, lower it). Check landscape stills (hook, a few questions before and after the reveal, outro). Post it once via the upload steps, but its `yt` title must not contain #shorts, the description should mention it's the weekly challenge and drop #shorts, and tags drop "shorts". (2026-11-15's challenge was posted as a Short before this change and stays up.)
5. Commit, push and notify the user with a short summary (views, subscribers, best format, any time change, challenge link).

## Content rules (monetisation safe)
- Original questions only; never copy other quiz channels. Rotate formats: flags, emoji (movies, food, animals, songs as titles only), science, space, human body, geography/capitals, true-or-false, odd one out, "which is bigger/older".
- Every answer must be correct and checkable; skip disputed or fast-changing facts. One short true fact per answer.
- No misleading claims: no "only 1% know", "99% fail", invented stats or "impossible". Honest hooks such as "Can you get all 5?".
- No logos, posters, screenshots, characters, song lyrics or outside music. Emoji, plain text and synthesised sound only.
- Vary `style`, `bg` and `layout` between consecutive quizzes. Keep text short, timer 3 s, length 30–45 s.
- Every quiz gets its own `yt.description`: one or two unique sentences about that quiz's actual content, then the hashtags. Never reuse a description template word for word. Titles must also be unique.
- Stick man reactor is built in (waves on the hook, thinks during the timer, gets nervous on the last second, celebrates at the answer, points to "Follow for a daily quiz!" at the end). Keep it; don't place new elements in the top corners where he stands.
- Narration is always on (Kokoro `af_heart`); the voice reads the hook, each question and the answer.
- Not made for kids; nothing violent, adult or political.
