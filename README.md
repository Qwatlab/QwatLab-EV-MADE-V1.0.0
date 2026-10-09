QwatLab EV-MADE V1.0.0
Please before using the software, please read the license, software instructions, about the software, and license requirements.
Dasturdan foydalanishdan avval litsenziya, dasturdan foydalanish yo'riqnomasi, dastur haqida va litsenziya  talablarini o'qib chiqing.

🇺🇿 Oʻzbek tilidagi tavsif
QwatLab EV-MADE V1.0.0 — elektr transport vositalarining harakat dinamikasi, elektr dvigateli, batareya tizimi, regenerativ tormozlanish, issiqlik boshqaruvi hamda holatni baholash jarayonlarini yagona hisoblash muhitida modellashtirish uchun moʻljallangan Python dasturiy platformasi.
Dasturiy platforma tavsifi
QwatLab EV-MADE V1.0.0 platformasi elektr transport vositalarining harakat dinamikasi, elektr dvigateli, batareya tizimi, regenerativ tormozlanish, issiqlik boshqaruvi hamda holatni baholash jarayonlarini yagona hisoblash muhitida modellashtirish uchun ishlab chiqilgan. Dastur Python dasturlash tilida yaratilgan bo‘lib, hozirgi rivojlanish bosqichida Streamlit freymvorkiga asoslangan interaktiv ilmiy-tadqiqot platformasi sifatida takomillashtirilmoqda.
Ushbu versiya foydalanuvchiga transport vositasi va batareya parametrlarini kiritish, harakat sikllarini qayta ishlash, kompleks elektro-termal hisoblashlarni amalga oshirish hamda olingan natijalarni grafik va jadval ko‘rinishida tahlil qilish va eksport qilish imkonini beradi.
Asosiy hisoblash va tahlil yo‘nalishlari
- QwatLab EV-MADE V1.0.0 quyidagi asosiy hisoblash va tahlil imkoniyatlarini o‘z ichiga oladi:
- Bo‘ylama harakat dinamikasi: aerodinamik qarshilik, dumalash qarshiligi, yo‘l qiyaligi va inertsiya kuchlarini hisoblash.
- Elektr dvigateli: motor momenti va quvvat chegaralarini hisobga olish.
- Tortish va ilashish: tortish kuchi hamda shina va yo‘l o‘rtasidagi ilashish chegaralarini baholash.
- Regenerativ tormozlanish: tormozlanish vaqtida energiyani qayta tiklash jarayonini modellashtirish.
- Batareyaning elektr modeli: batareya terminal kuchlanishi va elektr holatini hisoblash.
- Batareya toki va SOC: tok, C-rate va zaryad holati (SOC) o‘zgarishini aniqlash.
- Termal model: ikki tugunli (two-node) termal model asosida batareyaning issiqlik holatini baholash.
- Issiqlik boshqaruvi tizimi (TMS): batareya issiqlik rejimini boshqarish jarayonlarini modellashtirish.
- Holatni baholash: EKF (Extended Kalman Filter) va UKF (Unscented Kalman Filter) algoritmlari yordamida SOC holatini baholash.
- Energiya tahlili: harakat sikllari bo‘yicha energiya sarfi va samaradorlik ko‘rsatkichlarini hisoblash.
- Vizual tahlil: hisoblash natijalarini grafik va jadval ko‘rinishida taqdim etish.
- Ma’lumotlarni eksport qilish: keyingi ilmiy tahlil va qayta ishlash uchun hisoblash natijalarini eksport qilish.
Dasturiy arxitekturaning rivojlanishi va modullashtirish rejasi
Biz QwatLab EV-MADE loyihasini bosqichma-bosqich rivojlantirilayotgan ochiq dasturiy platforma sifatida shakllantirmoqdamiz. V1.0 versiyasida hisoblash algoritmlari, matematik modellar va foydalanuvchi interfeysi Streamlit muhiti doirasida integratsiyalangan.
Bunday yondashuv parametrlarni tezkor o‘zgartirish, turli hisoblash ssenariylarini bajarish, natijalarni vizual tahlil qilish va model komponentlarini bosqichma-bosqich takomillashtirish imkonini beradi.
Kelgusi versiyalarda hisoblash yadrosini Streamlit interfeysidan bosqichma-bosqich ajratish va dasturiy arxitekturani modulli shaklga o‘tkazishni rejalashtirganmiz. Loyihadagi asosiy modullar quyidagilardan iborat boʻladi:
1-bosqich. Modullarga bo`lish. GUI ni to`liq yadrodan ajratish:
1. GUI.py
2. Main.py
3. Data.py
4. Kinematics.py
5. Dynamics.py
6. Electrothernal.py
7. Export.py
2-bosqich. Backward va Forward facing usulini ishlab chiqish.
3-bosqich. Kengaytirish:
1. Transport vositasi dinamikasi moduli
2. Elektr dvigateli va transmissiya moduli
3. Batareya va BMS moduli
4. Issiqlik boshqaruvi moduli
5. Holatni baholash moduli
6. Harakat sikli va energiya tahlili moduli
7. Tahlil va ilmiy hisobot moduli
Ushbu modulli arxitektura hisoblash komponentlarini mustaqil ravishda rivojlantirishga yordam beradi. Ularni alohida test qilib, kelajakda turli ilmiy hamda web-interfeyslar bilan integratsiya qilish imkoniyatini yaratamiz.
V1.0 versiyasining ilmiy o‘rni
QwatLab EV-MADE V1.0 loyihaning muhim tayanch rivojlanish bosqichini ifodalaydi. Ushbu versiyada elektr transport vositasining mexanik, elektr va termal jarayonlarini yagona hisoblash muhitida o‘zaro bog‘langan holda tahlil qilish imkoniyati shakllantirilgan.
V1.0 versiyasi loyiha rivojlanishining yakuniy nuqtasi emas. U keyingi modullashtirish, hisoblash yadrosini interfeysdan ajratish va yangi funksional imkoniyatlarni qo‘shish uchun asos bo‘lib xizmat qiladi.
Mazkur versiyani DOI orqali arxivlash orqali dasturiy ta’minotning aniq versiyasini ilmiy tadqiqotlarda doimiy identifikatsiya qilamiz. Bu undan foydalanilgan hisoblash jarayonlarini xalqaro maqolalarda qayta takrorlash uchun muhim manba sifatida saqlash imkonini beradi.
QwatLab EV-MADE V1.0 shu tariqa loyihaning Streamlit asosidagi integratsiyalashgan ilmiy-tadqiqot platformasi sifatidagi joriy rivojlanish bosqichini aks ettiradi.

🇬🇧 English Description
Software Platform Overview
The QwatLab EV-MADE V1.0.0 platform models the driving dynamics, electric motor, battery system, regenerative braking, thermal management, and state estimation of electric vehicles within a single computational environment. We built this software in Python. In its current development phase, it operates as an interactive research platform based on the Streamlit framework.
This version allows users to input vehicle and battery parameters, process drive cycles, and execute complex electro-thermal calculations. Users can also analyze and export the results in graphical and tabular formats.
Core Computational and Analytical Features
QwatLab EV-MADE V1.0.0 includes the following capabilities:
- Longitudinal driving dynamics: calculating aerodynamic drag, rolling resistance, road gradient, and inertial forces.
- Electric motor: accounting for motor torque and power limits.
- Traction and adhesion: evaluating traction force and tire-road adhesion limits.
- Regenerative braking: modeling energy recovery during deceleration.
- Battery electrical model: computing battery terminal voltage and electrical state.
- Battery current and SOC: determining current, C-rate, and state of charge (SOC) variations.
- Thermal model: assessing battery thermal conditions using a two-node thermal model.
- Thermal Management System (TMS): simulating battery thermal management processes.
- State estimation: estimating SOC using Extended Kalman Filter (EKF) and Unscented Kalman Filter (UKF) algorithms.
- Energy analysis: calculating energy consumption and efficiency metrics across drive cycles.
- Visual analysis: presenting computational results in graphs and tables.
- Data export: exporting results for further scientific analysis and post-processing.
Software Architecture Evolution and Modularization Plan
We are developing the QwatLab EV-MADE project as an open software platform with a step-by-step evolution. Version 1.0.0 integrates computational algorithms, mathematical models, and the user interface directly within the Streamlit environment.
This approach enables rapid parameter modification, the execution of various computational scenarios, visual results analysis, and the gradual refinement of model components.
In future releases, we plan to separate the computational core from the Streamlit interface and transition the software architecture into a modular format. The planned core modules are:
Stage 1. Division into modules. Separate the full GUI from the kernel:
1. GUI.py
2. Main.py
3. Data.py
4. Kinematics.py
5. Dynamics.py
6. Electrothernal.py
7. Export.py
Stage 2. Development of the Backward and Forward facing method.
Stage 3. Extension:
1. Vehicle Dynamics Module
2. Electric Motor and Transmission Module
3. Battery and BMS Module
4. Thermal Management Module
5. State Estimation Module
6. Drive Cycle and Energy Analysis Module
7. Analysis and Scientific Reporting Module
This modular architecture will allow us to develop computational components independently. We can test them separately and integrate them with other scientific or web interfaces in the future.
Scientific Role of Version 1.0.0
QwatLab EV-MADE V1.0.0 represents a critical baseline development stage for the project. This version establishes the ability to analyze the mechanical, electrical, and thermal processes of an electric vehicle interdependently within a single computational environment.
Version 1.0.0 is not the final point of the project's development. It serves as the foundation for subsequent modularization, decoupling the computational core from the interface, and adding new functional capabilities.
Archiving this version via DOI ensures the permanent identification of this exact software version in scientific research. It preserves it as a vital resource for replicating the computational processes used in publications.
QwatLab EV-MADE V1.0.0 thus represents the current development stage of the project as a Streamlit-based integrated 
