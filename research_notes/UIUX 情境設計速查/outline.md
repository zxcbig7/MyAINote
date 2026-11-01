# UIUX Cheat Book Outline

定案日：2026-10-30。起點：讀者會開發頁面，但需要知道遇到具體使用情境時該選哪種設計。終點：能選元件、安排內容、處理完整狀態，並知道哪些要求是標準、平台慣例或待驗證的設計建議。

使用者指定情境速查格式，因此每條採「當……時，就應該……」＋正例、反例及必要邊界。研究三份已完成後才定案；原始 raw 來源保持不動。

## Part I — Visual Structure

1. Hierarchy：頁面先讓人看什麼。
2. Spacing：如何分組與控制密度。
3. Typography：文字角色、長文、混排與截斷。
4. Color：狀態、品牌色與 dark mode。
5. Shape：圓角幾何、裁切與 shape roles。
6. Responsive Layout：縮窄、鍵盤與安全區。
7. Navigation：任務入口、位置與返回。
8. Tabs and Disclosure：切換、閱讀與展開。
9. Search：搜尋範圍、成本與異步結果。
10. Filters：生效條件、組合邏輯與選取範圍。

## Part II — Controls and Operations

11. Actions：button/link、標籤與重複提交。
12. Choice Controls：單選、複選、即時開關與搜尋選取。
13. Fields：label、hint、格式與輸入負擔。
14. Validation：時機、修正、權限與服務錯誤。
15. Dates and Time：記憶日期、時段與跨時區。
16. Multi-step Work：往返、草稿與交易確認。
17. Identity and Onboarding：登入恢復、權限、初次任務。
18. Overlays：modal、drawer、popover、tooltip 與 focus。
19. Feedback and Waiting：通知、等待、取消與真實進度。
20. Empty and Destructive States：四種空狀態、Undo 與不可逆後果。

## Part III — Complex Workflows

21. Files and Persistence：上傳、autosave、offline 與衝突。
22. Tables and Bulk Actions：table/grid、比較、選取與批次失敗。
23. Pagination and Live Data：定位、返回、資料變動與同步。
24. Dashboards and Charts：指標、尺度、精確值與 drill-down。

## Part IV — Access and Quality

25. Touch and Motion：target size、gesture、drag 與 reduced motion。
26. Accessible Interaction：對比、reflow、keyboard、focus 與公告。
27. AI Interaction：生成、來源、審查、執行狀態與更正。
28. Systems and Validation：tokens、狀態、測試與誠實介面。

## Appendices

- Component selection：互斥選型矩陣，回連規則而不另計數。
- Page recipes：CRUD list/editor/login/dashboard/mobile filters/AI assistant 的規則組合。
- Evidence register：來源摘要、可點 URL、標準層級與適用範圍。
- Source boundary：原圓角筆記的條件補充與驗證時機分歧。
- Wiki links：MOC 與既有相關頁，更新 index、MOC 與 append-only log。

依賴檢查：先建立視覺與導航，再選 component；先處理單項輸入與回饋，再進批次、同步和 AI；accessibility 是所有章節的約束，專章提供數值查表與實測入口。
