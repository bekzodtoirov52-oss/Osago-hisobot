# Sug'urta Hisoboti (Streamlit App)

Excel fayllar asosida sug'urta kompaniyalari tushumi va foizlar taqsimotini avtomatlashtirilgan tarzda hisoblovchi veb-ilova.

### Asosiy vazifalar:
- `seria_polis` va `number_polis` ustunlarini bitta ustunga birlashtirish.
- `firstname` va `lastname` ustunlarini birlashtirish.
- **OSAGO** polislari uchun: 80% asosiy summa, 20% komissiya.
- **Boshqa barcha** polislar uchun: 75% asosiy summa, 25% komissiya.
- Har bir kompaniya bo'yicha jami polislar soni va alohida summalar hisob-kitobi.
- Barcha hisobotlar bo'yicha yakuniy **JAMI** qatori va Excel formatida yuklab olish imkoniyati.

### Mahalliy kompyuterda ishga tushirish:
```bash
pip install -r requirements.txt
streamlit run app.py
