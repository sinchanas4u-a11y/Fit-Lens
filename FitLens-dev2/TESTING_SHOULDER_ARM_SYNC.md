# Testing Guide: Shared Shoulder-Arm Coordinate Feature

## Test Setup

### Prerequisites
1. Backend server running (`python backend/app_updated.py`)
2. Frontend running (`npm start` in frontend-vite)
3. Test images ready (front view showing clear shoulders and arms)

## Test Cases

### Test Case 1: Basic Shoulder-Arm Connection (Left Side)

**Steps:**
1. Upload a front-view image
2. Enter height and select "Manual Mode"
3. Select "Shoulder Width" measurement type
4. Mark left shoulder point (click on left shoulder edge)
5. Mark right shoulder point (click on right shoulder edge)
6. Select "Arm Length" measurement type
7. **Observe**: Shoulder points should now be highlighted in GOLD
8. **Observe**: Yellow hint banner should appear: "💡 TIP: Start arm measurement from a shoulder point..."
9. Move cursor near left shoulder point
10. **Observe**: Green banner should appear: "✓ Snapping to left shoulder point"
11. Click near left shoulder (within 25 pixels)
12. **Verify**: Point should snap to exact shoulder coordinate
13. Click on wrist to complete arm measurement
14. Submit measurements

**Expected Backend Output:**
```
✓ DETECTED SHARED SHOULDER-ARM POINT (left side)
  Shoulder and arm measurements will use synchronized coordinates

Processing: Shoulder Width
  Original points: (120.0, 180.0) → (380.0, 180.0)
  Shared shoulder coordinate: (120.0, 180.0) → (118.5, 179.2)
  Using SHARED shoulder coordinate for point 1: (118.5, 179.2)
  Refined point 2: (381.3, 179.8)

Processing: Arm Length
  Original points: (120.0, 180.0) → (140.0, 420.0)
  Using SHARED shoulder coordinate for point 1: (118.5, 179.2)
  Refined point 2: (141.2, 421.5)
```

**Expected Measurements:**
- Shoulder width and arm length should share identical first coordinate
- Console should show "Snapped arm point to shoulder at: 120, 180" (or similar)

---

### Test Case 2: Shoulder-Arm Connection (Right Side)

**Steps:**
1. Follow steps 1-6 from Test Case 1
2. Move cursor near RIGHT shoulder point
3. **Observe**: Green banner: "✓ Snapping to right shoulder point"
4. Click near right shoulder
5. Click on wrist to complete arm measurement
6. Submit

**Expected Result:**
- Arm should connect to right shoulder
- Backend should detect "DETECTED SHARED SHOULDER-ARM POINT (right side)"
- Right shoulder coordinate should be shared between measurements

---

### Test Case 3: No Shoulder Marked (Independent Arm)

**Steps:**
1. Upload image
2. Select Manual Mode
3. Directly select "Arm Length" (without marking shoulder first)
4. **Observe**: No gold highlighting (no shoulder points exist)
5. **Observe**: Yellow hint still appears
6. Mark arm measurement normally (shoulder to wrist)
7. Submit

**Expected Result:**
- Arm measurement works independently
- No shared coordinate enforcement
- Normal edge refinement applied
- Backend should NOT show "DETECTED SHARED SHOULDER-ARM POINT"

---

### Test Case 4: Shoulder and Arm Not Connected

**Steps:**
1. Mark shoulder width
2. Mark arm length starting from a point MORE THAN 25 pixels away from shoulder
3. **Observe**: No snap feedback
4. **Observe**: Cursor doesn't magnetically snap
5. Submit

**Expected Result:**
- Backend should NOT detect shared point (distance > 20px threshold)
- Measurements processed independently
- No synchronized coordinates

---

### Test Case 5: Multiple Arms (Both Sides)

**Steps:**
1. Mark shoulder width
2. Mark LEFT arm (starting from left shoulder)
3. Mark RIGHT arm (starting from right shoulder)
4. Submit

**Expected Result:**
- Left arm uses left shoulder coordinate
- Right arm uses right shoulder coordinate
- Each arm-shoulder pair synchronized independently
- Backend shows two "DETECTED SHARED SHOULDER-ARM POINT" messages (left and right)

---

### Test Case 6: Visual Feedback Verification

**Steps:**
1. Mark shoulder width
2. Select "Arm Length"
3. **Visual Checks**:
   - [ ] Shoulder points are highlighted in GOLD color
   - [ ] Shoulder points have larger radius (10px vs 6px)
   - [ ] Shoulder points have pulsing outer ring
   - [ ] Yellow hint banner is visible
4. Move cursor near shoulder
5. **Visual Checks**:
   - [ ] Green snap confirmation banner appears
   - [ ] Cursor position visually snaps (magnetic effect)
6. Click on shoulder
7. **Visual Checks**:
   - [ ] Console logs "Snapped arm point to shoulder at: X, Y"

---

### Test Case 7: Edge Cases

#### 7a. Arm Endpoint at Shoulder
**Steps:**
1. Mark shoulder
2. Mark arm starting from wrist, ending at shoulder
3. Submit

**Expected**: System should detect shared endpoint and synchronize

#### 7b. Reversed Shoulder Order
**Steps:**
1. Mark shoulder width: right → left (instead of left → right)
2. Mark arm from shoulder
3. Submit

**Expected**: System should still detect shared point correctly

#### 7c. Delete and Remark
**Steps:**
1. Mark shoulder
2. Mark arm connected to shoulder
3. Delete arm measurement
4. Mark new arm measurement
5. Submit

**Expected**: New arm should also connect to shoulder

---

## Verification Checklist

### Frontend
- [ ] Shoulder points highlighted in gold when selecting arm length
- [ ] Yellow hint banner appears for arm length
- [ ] Green snap confirmation appears near shoulder
- [ ] Cursor snaps within 25px of shoulder
- [ ] Console logs snap events
- [ ] Visual feedback smooth and responsive

### Backend
- [ ] Console logs "DETECTED SHARED SHOULDER-ARM POINT"
- [ ] Shared coordinate logged in console
- [ ] "Using SHARED shoulder coordinate" message appears
- [ ] Same coordinate appears for shoulder and arm measurements
- [ ] Measurements calculated with shared coordinate
- [ ] No errors in backend console

### Measurements
- [ ] Shoulder width accurate
- [ ] Arm length accurate
- [ ] Both share identical shoulder coordinate (verify in JSON response)
- [ ] Edge refinement applied to shared point
- [ ] Visualization shows both measurements correctly

---

## Debug Tips

### If Snap Not Working:
1. Check console for errors
2. Verify shoulder measurement exists before arm
3. Check distance between points (should be < 25px)
4. Verify measurement types are 'shoulder' and 'arm'

### If Backend Not Detecting:
1. Check backend console for "DETECTED SHARED" message
2. Verify landmark types in request payload
3. Check point distance (should be < 20px backend threshold)
4. Verify landmarks array structure

### If Visual Feedback Missing:
1. Check if snapToShoulder state is updating
2. Verify selectedType === 'arm'
3. Check if shoulder landmarks exist in state
4. Verify findNearbyShoulderPoint returns non-null

---

## Success Criteria

✅ All test cases pass
✅ No console errors
✅ Visual feedback works smoothly
✅ Backend detects shared points correctly
✅ Measurements are synchronized
✅ Edge refinement applies to shared coordinates
✅ User experience is intuitive
✅ Documentation is clear

---

## Performance Expectations

- Snap detection: < 5ms (real-time, imperceptible)
- Visual feedback: Immediate (< 16ms for 60fps)
- Backend processing: < 100ms additional overhead
- No impact on other measurements
- Smooth user interaction
