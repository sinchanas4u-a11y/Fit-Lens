# Quick Test Guide: Manual Landmark Marking Feature

## 🚀 Quick Start (5 minutes)

### 1. Start the Servers

**Terminal 1 - Backend:**
```bash
cd c:\Users\sinch\Desktop\FitLens-dev3\FitLens-dev2\backend
python app_updated.py
```
✅ Should see: `Running on http://127.0.0.1:5001`

**Terminal 2 - Frontend:**
```bash
cd c:\Users\sinch\Desktop\FitLens-dev3\FitLens-dev2\frontend-vite
npm run dev
```
✅ Should see: `Local: http://localhost:3001/`

### 2. Open Browser
Navigate to: **http://localhost:3001**

---

## 🧪 Test Scenario 1: Manual Mode

1. Click **"Upload Mode"** button
2. Click **"Front View"** → Upload a full body photo
3. Enter **Height**: `175` cm
4. Click **"Process Images"** button
5. ✨ **Mode selection modal appears** (NEW!)
6. Click **"Manual Landmark Marking"**
7. Select **"Shoulder Width"** from dropdown
8. Click on **left shoulder** in the image
9. Click on **right shoulder** in the image
10. ✅ Blue line appears, measurement saved
11. Select **"Waist Width"** from dropdown
12. Click on **left waist**
13. Click on **right waist**
14. ✅ Another measurement saved
15. Click **"Complete Marking"** button
16. ✅ Results appear with measurements in cm!

**Expected Result:**
- Mode badge shows "✋ Manual Mode"
- Yellow info box: "Showing only the measurements you marked"
- Table shows: Shoulder width ~40-50cm, Waist width ~30-40cm

---

## 🤖 Test Scenario 2: Automatic Mode

1. Click **"Process New Images"** to reset
2. Upload same photo
3. Enter same height
4. Click **"Process Images"**
5. Click **"Automatic Detection"** (marked as Recommended)
6. ⏳ Watch processing steps (6 steps)
7. ✅ Results appear with 8+ measurements!

**Expected Result:**
- Mode badge shows "🤖 Automatic Mode"
- Landmarks visualization displayed
- Segmentation mask displayed
- 8+ measurements in table

---

## 🔍 Quick Troubleshooting

### Mode Selection Doesn't Appear
- Press **F12** → Console tab
- Look for: `🚀 Starting automatic image processing...`
- If you see this immediately, the new code isn't being used
- **Fix**: Hard refresh browser (Ctrl+Shift+R)

### Canvas Shows Blank
- Check browser console for errors
- Verify image uploaded successfully
- **Fix**: Try a different image format (JPG/PNG)

### Backend Error
- Check backend terminal for red error text
- Common issue: `mediapipe` not installed
- **Fix**: `pip install mediapipe==0.10.14`

### Frontend Build Error
- Check frontend terminal for errors
- **Fix**: `npm install` then `npm run dev`

---

## 📸 Best Test Images

**Good for Manual Mode:**
- Full body photo
- Standing straight
- Arms slightly away from body
- Good lighting
- Clear silhouette

**Good for Automatic Mode:**
- Same as manual mode
- Plus: Face visible (for landmark detection)
- Plus: Minimal background clutter

---

## ✅ Success Criteria

**Manual Mode Works When:**
- [x] Mode selection modal appears after "Process Images"
- [x] Canvas loads with image
- [x] Clicking places blue points
- [x] Line connects two points
- [x] Measurements appear in sidebar
- [x] "Complete Marking" processes data
- [x] Results show measurements in cm
- [x] Manual mode badge visible

**Automatic Mode Works When:**
- [x] Mode selection modal appears
- [x] "Automatic Detection" starts processing
- [x] 6 steps show progress
- [x] Results include 8+ measurements
- [x] Landmarks visualization shown
- [x] Automatic mode badge visible

---

## 🎯 Key Features to Test

### Manual Marking Canvas
- [ ] Select different landmark types
- [ ] Place points on image
- [ ] See distance in pixels
- [ ] Hover over points (scale effect)
- [ ] Delete a measurement
- [ ] Complete marking

### Mode Selection
- [ ] Modal appears after "Process Images"
- [ ] Both cards visible
- [ ] "Recommended" badge on Automatic
- [ ] Cancel modal
- [ ] Select manual mode
- [ ] Select automatic mode

### Results Display
- [ ] Mode badge shows correct mode
- [ ] Manual: Yellow info box
- [ ] Manual: Only marked measurements
- [ ] Automatic: All measurements
- [ ] Measurements in cm are reasonable
- [ ] Can download JSON

---

## 🐛 Common Issues

**Issue**: "Module 'mediapipe' has no attribute 'solutions'"
**Fix**: Already fixed! Backend uses fallback import.

**Issue**: Mode selection modal doesn't close
**Fix**: Click outside modal or use Cancel button.

**Issue**: Manual marking canvas is cut off
**Fix**: Canvas auto-scales. Try resizing browser window.

**Issue**: Measurements seem wrong
**Fix**: Check that height was entered correctly (cm vs inches).

---

## 📋 Quick Checklist

Before testing:
- [ ] Backend server running on port 5001
- [ ] Frontend server running on port 3001
- [ ] Browser open to http://localhost:3001
- [ ] Test image ready (full body photo)

Files modified:
- [ ] `frontend-vite/src/components/UploadMode.jsx` (updated)
- [ ] `frontend-vite/src/components/ModeSelection.jsx` (new)
- [ ] `frontend-vite/src/components/ModeSelection.css` (new)
- [ ] `frontend-vite/src/components/ManualLandmarkMarker.jsx` (new)
- [ ] `frontend-vite/src/components/ManualLandmarkMarker.css` (new)
- [ ] `backend/app_updated.py` (updated with /api/process-manual)

---

## 🎉 Success!

If you can:
1. See the mode selection modal ✅
2. Use manual marking to place points ✅
3. Get measurement results in cm ✅
4. Switch between manual/automatic modes ✅

**Then the feature is working perfectly!**

---

## 📚 More Details

See [MANUAL_LANDMARK_FEATURE.md](MANUAL_LANDMARK_FEATURE.md) for:
- Complete technical documentation
- API reference
- Architecture details
- Development notes
- Future enhancements

---

*Happy Testing! 🎉*
