;Language: Sundanese  (33)
;By sukma gemala - http://facebook.com/sukma.gemala

!insertmacro LANGFILE "Sundanese" = "Basa Sunda" =

!ifdef MUI_WELCOMEPAGE
  ${LangFileString} MUI_TEXT_WELCOME_INFO_TITLE "Bag�a, ieu t�h Apingan Masang $(^NameDA)"
  ${LangFileString} MUI_TEXT_WELCOME_INFO_TEXT "Apingan Masang bakal ngaping anjeun dina pros�s masangkeun $(^NameDA).$\r$\n$\r$\nAlusna mah tutupkeun heula program s�j�n anu ayeuna keur dijalankeun sam�m�h nuluykeun masang ieu program. Eta hal aya patalina jeung kaperluan ngarobah file anu keur dipak� ku sistem tanpa kudu ngamimitian-deui (restart) komputer anjeun.$\r$\n$\r$\n$_CLICK"
!endif

!ifdef MUI_UNWELCOMEPAGE
  ${LangFileString} MUI_UNTEXT_WELCOME_INFO_TITLE "Bag�a, ieu t�h Apingan Miceun $(^NameDA)"
  ${LangFileString} MUI_UNTEXT_WELCOME_INFO_TEXT "Apingan Miceun bakal ngaping anjeun dina pros�s miceun $(^NameDA).$\r$\n$\r$\nSamemeh ngamimitian miceun instalasina, anjeun kudu yakin heula y�n $(^NameDA) henteu eukeur dijalankeun.$\r$\n$\r$\n$_CLICK"
!endif

!ifdef MUI_LICENSEPAGE
  ${LangFileString} MUI_TEXT_LICENSE_TITLE "Aturan jeung Kasapukan"
  ${LangFileString} MUI_TEXT_LICENSE_SUBTITLE "Imeutan ieu aturan jeung kasapukan sam�m�h masangkeun $(^NameDA)."
  ${LangFileString} MUI_INNERTEXT_LICENSE_BOTTOM "Lamun anjeun narima sakab�h anu dipedar, klik Sapuk pikeun nuluykeun. Anjeun kudu satuju sangkan bisa masangkeun $(^NameDA)."
  ${LangFileString} MUI_INNERTEXT_LICENSE_BOTTOM_CHECKBOX "Lamun anjeun narima sakab�h anu dipedar dina kasapukan, b�r� contr�ng. Anjeun kudu satuju sangkan bisa masangkeun $(^NameDA). $_CLICK"
  ${LangFileString} MUI_INNERTEXT_LICENSE_BOTTOM_RADIOBUTTONS "Lamun anjeun narima sakab�h anu dipedar dina kasapukan, pilih salah sahiji anu aya dihandap. Anjeun kudu satuju sangkan bisa masangkeun $(^NameDA). $_CLICK"
!endif

!ifdef MUI_UNLICENSEPAGE
  ${LangFileString} MUI_UNTEXT_LICENSE_TITLE "Aturan jeung Kasapukan"
  ${LangFileString} MUI_UNTEXT_LICENSE_SUBTITLE "Imeutan ieu aturan jeung kasapukan sam�m�h miceun $(^NameDA)."
  ${LangFileString} MUI_UNINNERTEXT_LICENSE_BOTTOM "Lamun anjeun narima sakab�h anu dipedar, klik Sapuk pikeun nuluykeun. Anjeun kudu satuju sangkan bisa miceun $(^NameDA)."
  ${LangFileString} MUI_UNINNERTEXT_LICENSE_BOTTOM_CHECKBOX "Lamun anjeun narima sakab�h anu dipedar dina kasapukan, b�r� contr�ng. Anjeun kudu satuju sangkan bisa miceun $(^NameDA). $_CLICK"
  ${LangFileString} MUI_UNINNERTEXT_LICENSE_BOTTOM_RADIOBUTTONS "Lamun anjeun narima sakab�h anu dipedar dina kasapukan, pilih salah sahiji anu aya dihandap. Anjeun kudu satuju sangkan bisa miceun $(^NameDA). $_CLICK"
!endif

!ifdef MUI_LICENSEPAGE | MUI_UNLICENSEPAGE
  ${LangFileString} MUI_INNERTEXT_LICENSE_TOP "Penc�t Page Down pikeun ningali tuluyanana."
!endif

!ifdef MUI_COMPONENTSPAGE
  ${LangFileString} MUI_TEXT_COMPONENTS_TITLE "Milih Kompon�n"
  ${LangFileString} MUI_TEXT_COMPONENTS_SUBTITLE "Pilih fitur ti $(^NameDA) anu r�k dipasang."
  ${LangFileString} MUI_INNERTEXT_COMPONENTS_DESCRIPTION_TITLE "Wangenan"
!endif

!ifdef MUI_UNCOMPONENTSPAGE
  ${LangFileString} MUI_UNTEXT_COMPONENTS_TITLE "Milih Kompon�n"
  ${LangFileString} MUI_UNTEXT_COMPONENTS_SUBTITLE "Pilih fitur ti $(^NameDA) anu r�k dipiceun."
!endif

!ifdef MUI_COMPONENTSPAGE | MUI_UNCOMPONENTSPAGE
  !ifndef NSIS_CONFIG_COMPONENTPAGE_ALTERNATIVE
    ${LangFileString} MUI_INNERTEXT_COMPONENTS_DESCRIPTION_INFO "Tunjuk salah sahiji pikeun ningali kateranganana."
  !else
    ${LangFileString} MUI_INNERTEXT_COMPONENTS_DESCRIPTION_INFO "Tunjuk salah sahiji pikeun ningali kateranganana."
  !endif
!endif

!ifdef MUI_DIRECTORYPAGE
  ${LangFileString} MUI_TEXT_DIRECTORY_TITLE "Milih Lokasi Masang"
  ${LangFileString} MUI_TEXT_DIRECTORY_SUBTITLE "Pilih map pikeun tempat masangkeun $(^NameDA)."
!endif

!ifdef MUI_UNDIRECTORYSPAGE
  ${LangFileString} MUI_UNTEXT_DIRECTORY_TITLE "Milih Lokasi Miceun"
  ${LangFileString} MUI_UNTEXT_DIRECTORY_SUBTITLE "Pilih map pikeun tempat miceun $(^NameDA)."
!endif

!ifdef MUI_INSTFILESPAGE
  ${LangFileString} MUI_TEXT_INSTALLING_TITLE "Masang"
  ${LangFileString} MUI_TEXT_INSTALLING_SUBTITLE "Tungguan,  $(^NameDA) eukeur dipasangkeun."
  ${LangFileString} MUI_TEXT_FINISH_TITLE "Pros�s Masangkeun R�ngs�"
  ${LangFileString} MUI_TEXT_FINISH_SUBTITLE "$(^NameDA) r�ngs� dipasangkeun."
  ${LangFileString} MUI_TEXT_ABORT_TITLE "Pros�s Masang Dibolaykeun"
  ${LangFileString} MUI_TEXT_ABORT_SUBTITLE "Masangkeun r�ngs� tapi can sampurna."
!endif

!ifdef MUI_UNINSTFILESPAGE
  ${LangFileString} MUI_UNTEXT_UNINSTALLING_TITLE "Miceun"
  ${LangFileString} MUI_UNTEXT_UNINSTALLING_SUBTITLE "Tungguan,  $(^NameDA) eukeur dipiceun."
  ${LangFileString} MUI_UNTEXT_FINISH_TITLE "Pros�s Miceun R�ngs�"
  ${LangFileString} MUI_UNTEXT_FINISH_SUBTITLE "$(^NameDA) r�ngs� dipiceun."
  ${LangFileString} MUI_UNTEXT_ABORT_TITLE "Pros�s Miceun Dibolaykeun"
  ${LangFileString} MUI_UNTEXT_ABORT_SUBTITLE "Miceun r�ngs� tapi can sampurna."
!endif

!ifdef MUI_FINISHPAGE
  ${LangFileString} MUI_TEXT_FINISH_INFO_TITLE "Ngar�ngs�keun Apingan Masang $(^NameDA)"
  ${LangFileString} MUI_TEXT_FINISH_INFO_TEXT "$(^NameDA) geus dipasangkeun kana komputer anjeun.$\r$\n$\r$\nKlik R�ngs� pikeun nutup Apingan Masang."
  ${LangFileString} MUI_TEXT_FINISH_INFO_REBOOT "Komputer anjeun kudu dimimitian-deui (restart) pikeun ngar�ngs�keun pros�s instalasi $(^NameDA). Mmimitian-deui ayeuna?"
!endif

!ifdef MUI_UNFINISHPAGE
  ${LangFileString} MUI_UNTEXT_FINISH_INFO_TITLE "Ngar�ngs�keun Apingan Miceun $(^NameDA)"
  ${LangFileString} MUI_UNTEXT_FINISH_INFO_TEXT "$(^NameDA) geus dipiceun tina komputer anjeun.$\r$\n$\r$\nKlik R�ngs� pikeun nutup Apingan Miceun."
  ${LangFileString} MUI_UNTEXT_FINISH_INFO_REBOOT "Komputer anjeun kudu dimimitian-deui (restart) pikeun ngar�ngs�keun pros�s uninstall $(^NameDA). Mmimitian-deui ayeuna?"
!endif

!ifdef MUI_FINISHPAGE | MUI_UNFINISHPAGE
  ${LangFileString} MUI_TEXT_FINISH_REBOOTNOW "Mimitian-deui"
  ${LangFileString} MUI_TEXT_FINISH_REBOOTLATER "Moal waka"
  ${LangFileString} MUI_TEXT_FINISH_RUN "&Jalankeun $(^NameDA)"
  ${LangFileString} MUI_TEXT_FINISH_SHOWREADME "&Buka Koropak Bacaheula"
  ${LangFileString} MUI_BUTTONTEXT_FINISH "&R�ngs�"
!endif

!ifdef MUI_STARTMENUPAGE
  ${LangFileString} MUI_TEXT_STARTMENU_TITLE "Milih Menu Mimiti"
  ${LangFileString} MUI_TEXT_STARTMENU_SUBTITLE "Pilih map Menu Mimiti (Start Menu) pikeun nempatkeun tumbu $(^NameDA)."
  ${LangFileString} MUI_INNERTEXT_STARTMENU_TOP "Pilih map Menu Mimiti (Start Menu) pikeun nempatkeun tumbu ieu program. Og� bisa nyieun ngaran map anyar."
  ${LangFileString} MUI_INNERTEXT_STARTMENU_CHECKBOX "Ulah nyieun tumbu"
!endif

!ifdef MUI_UNCONFIRMPAGE
  ${LangFileString} MUI_UNTEXT_CONFIRM_TITLE "Miceun $(^NameDA)"
  ${LangFileString} MUI_UNTEXT_CONFIRM_SUBTITLE "Miceun $(^NameDA) tina komputer anjeun."
!endif

!ifdef MUI_ABORTWARNING
  ${LangFileString} MUI_TEXT_ABORTWARNING "Bener, r�k kaluar tina pros�s masangkeun $(^Name)?"
!endif

!ifdef MUI_UNABORTWARNING
  ${LangFileString} MUI_UNTEXT_ABORTWARNING "Bener, r�k kaluar tina pros�s miceun $(^Name)?"
!endif

!ifdef MULTIUSER_INSTALLMODEPAGE
  ${LangFileString} MULTIUSER_TEXT_INSTALLMODE_TITLE "Milih Pamak�"
  ${LangFileString} MULTIUSER_TEXT_INSTALLMODE_SUBTITLE "Milih pamak� anu r�k dipasangkeun $(^NameDA)."
  ${LangFileString} MULTIUSER_INNERTEXT_INSTALLMODE_TOP "Pilih tujuan masangkeun $(^NameDA) keur soranganeun atawa keur kab�h pamak� komputer ieu. $(^ClickNext)"
  ${LangFileString} MULTIUSER_INNERTEXT_INSTALLMODE_ALLUSERS "Pasangkeun keur kab�h pamak� komputer ieu"
  ${LangFileString} MULTIUSER_INNERTEXT_INSTALLMODE_CURRENTUSER "Kuring wungkul"
!endif
