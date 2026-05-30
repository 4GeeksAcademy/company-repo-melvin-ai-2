# Mobile & Device Testing Checklist for Brasaland Website

## 1. General
- [ ] Viewport meta tag present
- [ ] Responsive layout (flex/grid, Tailwind responsive classes)
- [ ] No horizontal scrolling on mobile
- [ ] Font sizes readable on all devices
- [ ] Color contrast accessible
- [ ] Skip links and keyboard navigation work

## 2. Navigation & Buttons
- [ ] Navigation is visible and usable on all screen sizes
- [ ] Buttons are at least 48x48px for touch
- [ ] Tap targets are not too close together
- [ ] Focus states visible for all interactive elements

## 3. Forms (signup.html)
- [ ] Inputs are easy to tap and fill on mobile
- [ ] Labels are visible and clear
- [ ] Error messages are readable
- [ ] Form submits and displays feedback correctly

## 4. Content
- [ ] Headings and text do not overflow
- [ ] Lists and sections stack vertically on small screens
- [ ] Images (if present) are responsive (w-full, h-auto)
- [ ] No content is cut off or hidden

## 5. Performance
- [ ] Loads quickly on 3G/4G
- [ ] No large unoptimized images
- [ ] Minimal blocking scripts

## 6. Device & Browser Coverage
Test on:
- [ ] iPhone (Safari, Chrome)
- [ ] Android phone (Chrome, Firefox)
- [ ] iPad/tablet (Safari, Chrome)
- [ ] Desktop (Chrome, Firefox, Edge, Safari)

## 7. Accessibility
- [ ] All content reachable by keyboard
- [ ] Screen reader announces headings, links, buttons
- [ ] Sufficient color contrast
- [ ] No flashing or moving content that can’t be paused

---

**Tip:** Use browser dev tools to simulate devices and test touch/keyboard navigation. For real-world testing, try BrowserStack, Sauce Labs, or physical devices.
