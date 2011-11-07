# Bez polskich znakow, please!
# Cokolwiek robimy staramy sie nazywac przejrzyscie (tj. raczej 'wykres_wykladnika_od_spostrzegawczosci" niz "wyk4"),
# a takze obficie i rzetelnie komentujemy.

# n - aktualna liczba wszystkich graczy
# m - aktualna liczba mafiozow

# Do czego ma sluzyc:
# - numerycznego modelowania gry w mafie w oparciu o rozne proste modele wymiany informcacji i glosowania
# - dodawania Kataniego i Kurtyzany
# - raczej do gry bez odkrywania kart jak ktos zginie (modelowanie z odkrywaniem byloby trudniejsze
# bo byloby znacznie wiecej czesc i taktycznej itd)

# Importujemy to czy owo. Najlepiej bez fraz 'from costam import *', co przy dluzszym projekcie moga
# przypadkiem sie pojawic rzeczy o tej samej nazwie z innych modulow, a tego nie chcemy.

import numpy as np
import random
import matplotlib.pyplot as p
import math


#
# STRATEGIE I MOZLIWE DZIALANIA W DZIEN I W NOCY
#


# generuj_postacie
# Funkcja zwracajaca liste literek, odpowiadajacych typom postaci.
# Standardowo 'm' to mafioza, 'c' to zwykly miastowy, 'k' to Katani a 'd' to martwy.

def mafia_i_miastowi( n, m, **dod_arg ):
    return (['m'] * m) + (['c'] * ( n - m ))
    
def mafia_i_miastowi_z_katanim( n, m, **dod_arg ):
    return (['m'] * m) + (['c'] * ( n - m - 1)) + ['k']
    

# faza_dyskusji
# w czasie fazy dyskusji dochodzi do zmiany podejrzen - zarowno analizy porzedniego linczu, tego kto zostal zabity w nocy, obserwacji, jak i - wymiany informacji
# kto_kogo_podejrzewa[i][j] - jak bardzo i-ty gracz chce ubic j-tego

# kazdy losowo podejrzewa, inaczej w kazdej turze
def losowe_podejrzenia( n, m, kto_jest_kim, kto_kogo_podejrzewa, m_poczatkowe, kto_na_kogo_glosowal, ostatnio_zabity, **dodatkowe_argumetny):
    for i in range( len( kto_kogo_podejrzewa ) ):
        for j in range( len( kto_kogo_podejrzewa ) ):
            if (kto_jest_kim[i] != 'd') and (kto_jest_kim[j] != 'd'): # martwi nie glosuja, na martwych sie nie glosuje
                kto_kogo_podejrzewa[i][j] = random.random()
            else:
                kto_kogo_podejrzewa[i][j] = 0

def obserwacja( n, m, kto_jest_kim, kto_kogo_podejrzewa, m_poczatkowe, kto_na_kogo_glosowal, ostatnio_zabity,
spostrzegawczosc = 1., udawana_spostrzegawczosc_mafii = 0., **dodatkowe_argumetny ):
    for i in range( len( kto_kogo_podejrzewa ) ):
        if kto_jest_kim[i] == 'm':
            for j in range( len( kto_kogo_podejrzewa ) ):
                if kto_jest_kim[j] == 'm':
                    kto_kogo_podejrzewa[i][j] += (1 + (udawana_spostrzegawczosc_mafii / n)) * random.random()
                elif kto_jest_kim[j] != 'd': #zakladamy implicite, ze dodatkowe postacie sa z miasta
                    kto_kogo_podejrzewa[i][j] += 1 * random.random()
        elif kto_jest_kim[i] != 'd': #zakladamy implicite, ze dodatkowe postacie sa z miasta
            for j in range( len( kto_kogo_podejrzewa ) ):
                if kto_jest_kim[j] == 'm':
                    kto_kogo_podejrzewa[i][j] += (1 + (spostrzegawczosc / n)) * random.random()
                elif kto_jest_kim[j] != 'd': #zakladamy implicite, ze dodatkowe postacie sa z miasta
                    kto_kogo_podejrzewa[i][j] += 1 * random.random()

# faza_linczowania
# w czasie fazy linczowania gracze oddaja glos
# - czy gracze glosuja 'za glosem serca' czy tez np sa wysuwane 3 kandydatury i sie do nich dostosowuja, czy np. gracze staraja sie akumulowac glosy
# - jak przekladaja sie glosy na zabijanie (mozna rozwazyc np. model gdzie w razie remisu nikt nie ginie)

def proste_linczowanie( n, m, kto_jest_kim, kto_kogo_podejrzewa, kto_na_kogo_glosowal, kto_podpadl_mafii, **dodatkowe_argumetny ):
# kazdy glosuje zgodnie z preferencjami, w przypadku remisu ginie losowa osoba z remisujacych
    kto_na_kogo_glosowal = np.zeros( [ len(kto_jest_kim) ], int ) - 1
    glosy_na_dana_osobe = np.zeros( [ len(kto_jest_kim) ], int )
    for i in range( len( kto_jest_kim ) ):
        if kto_jest_kim[i] != 'd': # kazdy zywy glosuje
            kto_na_kogo_glosowal[i] = kto_kogo_podejrzewa[i].argmax()
            glosy_na_dana_osobe[ kto_na_kogo_glosowal[i] ] += 1
    # teraz bawimy sie remisem
    max_glosow = max( glosy_na_dana_osobe )
    zwyciezcy = list( i for i in range( len( glosy_na_dana_osobe )) if glosy_na_dana_osobe[i] == max_glosow )
    ostatnio_zlinczowany = random.sample( zwyciezcy, 1 )[0]
    # a teraz outcome
    if kto_jest_kim[ ostatnio_zlinczowany ] == 'm':
        m += -1
    kto_jest_kim[ ostatnio_zlinczowany ] = 'd'
    return ( n - 1, m, ostatnio_zlinczowany )
        

# faza_nocna
# W czasie niej mafia zabija swoja ofiare i dzialaja inne ewentualne frakcje nocne.
# Zmienia n,m, kto_jest_kim (bo ktos zwykle 'sie' przekreca) i ew. tabele podejrzanosci, np. w przypadku gdy Katani sprawdza
def mafia_zabija_losowego_miastowego( n, m, kto_jest_kim, kto_kogo_podejrzewa, kto_podpadl_mafii, **dodatkowe_argumetny ):
    numerki_miastowych = list( i for i in range( len( kto_jest_kim )) if ( (kto_jest_kim[i] != 'm') and (kto_jest_kim[i] != 'd') ) )
    # ^ znow zakladamy implicite, ze nie-mafiozi to miastowi
    ostatnio_zabity = random.sample( numerki_miastowych, 1)[0]
    kto_jest_kim[ ostatnio_zabity ] = 'd'
    return (n - 1, m, ostatnio_zabity )

def modyfikacja_podpadniecia_mafii(n, m, kto_kogo_podejrzewa, kto_podpadl_mafii, m_poczatkowe, kto_jest_kim):
    for i in range(m_poczatkowe):
        if kto_jest_kim[i] != 'd':  #oczywiscie, glosuja zywi
            numerki_miastowych=[]
            for x in range(len(kto_kogo_podejrzewa)):
                           if kto_jest_kim[x] != 'd':
                               if kto_jest_kim[x] != 'm':
                                   if kto_kogo_podejrzewa[x].argmax() == i:  #jezeli ktos zaglosuje na mafioze, to mafia chce go zabic
                                       numerki_miastowych.append(x)
            if len(numerki_miastowych)!=0:
                wybor=random.sample(numerki_miastowych, 1)[0]
            else:
                     numerki_miastowych = list( i for i in range( len( kto_jest_kim )) if ( (kto_jest_kim[i] != 'm') and (kto_jest_kim[i] != 'd') ) )  #jak nikt nie zaglosowal na mafie, to losujemy kogo usmiercic
                     wybor=random.sample( numerki_miastowych, 1)[0]
            kto_podpadl_mafii[wybor]+=1  #rosnie ilosc glosow na dana osobe


def mafia_zemsta(n, m, kto_jest_kim, kto_na_kogo_glosowal, kto_podpadl_mafii, **dodatkowe_argumetny):   #w tej funkcji mafia glosuje w nocy na tych, ktorzy atakowali mafie 
    numerki_miastowych=[]
    #print kto_podpadl_mafii
    max_glosow = max( kto_podpadl_mafii )
    #print max_glosow
    for x in range(len(kto_na_kogo_glosowal)):
                      if kto_podpadl_mafii[x] == max_glosow:
                          numerki_miastowych.append(x)
    #print numerki_miastowych
    ostatnio_zabity = random.sample( numerki_miastowych , 1)[0]  #losujemy tych z najwieksza iloscia glosow
    kto_jest_kim[ ostatnio_zabity ] = 'd'
    return (n - 1, m, ostatnio_zabity )

            
                           


#
# GLOWNA FUNKCJA
#


# Glowna funkcja przeprowadzajace gre w mafie. Jesli chcesz zrobic funkcje zwracajaca jako wynik np.
# log z podejrzen, albo liczebnosci mafiozow (czy tez cokolwiek wypisujaca w czasie rzeczywistym),
# zrob osobna funkcje.

def kto_wygral_jedna_gre( n_poczatkowe , m_poczatkowe,
generuj_postacie = mafia_i_miastowi, faza_dyskusji = losowe_podejrzenia, decyzja_mafii=modyfikacja_podpadniecia_mafii,
faza_linczowania = proste_linczowanie, faza_nocna = mafia_zabija_losowego_miastowego,
wypisuj = False, kto_podpadl=modyfikacja_podpadniecia_mafii, **dodatkowe_argumetny):
    n = n_poczatkowe
    m = m_poczatkowe
    kto_jest_kim = generuj_postacie( n_poczatkowe , m_poczatkowe, **dodatkowe_argumetny)
    if wypisuj:
        print kto_jest_kim
    kto_kogo_podejrzewa = np.zeros( [n_poczatkowe, n_poczatkowe] )
    # kto_kogo_podejrzewa[i][j] - jak bardzo i-ty gracz chce ubic j-tego
    kto_na_kogo_glosowal = np.zeros( [n_poczatkowe], int ) - 1 # na i-ym miejscu jest glos i-tej osoby
    #kto_podpadl_mafii = np.zeros( [n_poczatkowe], int)
    ostatnio_zabity = -1
    # ^ ostatnio nikt nie byl zabity wiec dajemy -1
    while n > m:
        kto_podpadl_mafii = np.zeros( [n_poczatkowe], int)
        faza_dyskusji( n, m, kto_jest_kim, kto_kogo_podejrzewa, m_poczatkowe, kto_na_kogo_glosowal, ostatnio_zabity, **dodatkowe_argumetny)
        # ^ modyfikuje tylko kto_kogo_podejrzewa
        decyzja_mafii(n, m, kto_kogo_podejrzewa, kto_podpadl_mafii, m_poczatkowe, kto_jest_kim, **dodatkowe_argumetny)    #strategia mafii podczas dnia. Jezeli proste_linczowanie bierzemy, to ten fragment nie ma znaczenia
        # modyfikuje kto_podpadl_mafii
        #print kto_podpadl_mafii
        ( n, m, ostatnio_zlinczowany ) = faza_linczowania( n, m, kto_jest_kim, kto_kogo_podejrzewa, kto_na_kogo_glosowal, kto_podpadl_mafii, **dodatkowe_argumetny )
        # ^ modyfikuje tylko n, m, ostatnio_zlinczowany i kto_jest_kim
        if wypisuj:
            print ostatnio_zlinczowany, 'zostal zlinczowany.'
            print kto_jest_kim
        if ( m == 0 or n - m == 0 ):
            break
        kto_podpadl_mafii = np.zeros( [n_poczatkowe], int)
        kto_podpadl(n, m, kto_kogo_podejrzewa, kto_podpadl_mafii, m_poczatkowe, kto_jest_kim, **dodatkowe_argumetny)
        #modyfikuje tylko kto_podpadl_mafii
        #print 'Noc:'
        #print kto_podpadl_mafii
        ( n, m, ostatnio_zabity ) = faza_nocna( n, m, kto_jest_kim, kto_kogo_podejrzewa, kto_podpadl_mafii, **dodatkowe_argumetny )
        # ^ modyfikuje n, m, kto_jest_kim, ostatnio_zabity i kto_kogo_podejrzewa (to ostatnie w przypadku np. Kataniego)
        if wypisuj:
            print ostatnio_zabity, 'zostal zamordowany.'
            print kto_jest_kim
    if m > 0:
        if wypisuj:
            print 'Wygrala mafia!'
        return 1
    else:
        if wypisuj:
            print 'Wygrali miastowi!'
        return 0



#
# SKANOWANIE, WYKRESLANIE ITD
#


def skanuj_dla_jednego_mafiozo( n_min, n_max, ile_razy, **argumenty):
    return list(
    [ n, sum( list( kto_wygral_jedna_gre( n, 1, **argumenty) for i in range( ile_razy) ) ) / float( ile_razy ) ]
    for n in range(n_min, n_max + 1)
    )


# TO DO:
# - dopasowanie w(n,m) = stala n^gamma, wraz z niepewnosciami
# - wykreslanie wynikow, wraz z dopasowaniem i stosownymi podpisami
# - skanowanie gamm dla roznych spostrzegawczosci, a takze wykreslanie tego
# - inne strategie w ciagu dnia i nocy, Katani, ...
# - cala pula innych pomyslow :)


def obserwacja_obywatele(n, m, kto_jest_kim, kto_kogo_podejrzewa, m_poczatkowe, kto_na_kogo_glosowal, ostatnio_zabity,
spostrzegawczosc = 1., udawana_spostrzegawczosc_mafii = 0., **dodatkowe_argumetny):     #funkcja obserwacji, ale tylko dla obywateli, czyli wtedy gdy chcemy, aby mafia dzialala z jakas strategia w ciagu dnia
        for i in range(m_poczatkowe, len( kto_kogo_podejrzewa ) ):
            if kto_jest_kim[i] != 'm':   #glosuja tylko zywi obywatele
                if kto_jest_kim[i] != 'd':
                    for j in range( len( kto_kogo_podejrzewa ) ):
                        if kto_jest_kim[j] == 'm':
                            kto_kogo_podejrzewa[i][j] += (1 + (spostrzegawczosc/ n)) * random.random()
                        elif kto_jest_kim[j] != 'd': #zakladamy implicite, ze dodatkowe postacie sa z miasta
                            kto_kogo_podejrzewa[i][j] += 1 * random.random()

def linczowanie_z_strategia_zemsta(n, m, kto_jest_kim, kto_kogo_podejrzewa, kto_na_kogo_glosowal, kto_podpadl_mafii, **dodatkowe_argumetny):   #funkcja dnia, w ktorej mafia glosuje na tych, ktorzy glosuja na nia. Na razie mafia glosuje jednomyslnie
    kto_na_kogo_glosowal = np.zeros( [ len(kto_jest_kim) ], int ) - 1
    glosy_na_dana_osobe = np.zeros( [ len(kto_jest_kim) ], int )
    numerki_miastowych=[]
    max_glosow = max( kto_podpadl_mafii ) #najpierw glosuje mafia, wg tego co wczesniej ustalili
    for x in range(len(kto_na_kogo_glosowal)):   
                      if kto_podpadl_mafii[x] == max_glosow:
                          numerki_miastowych.append(x)
    cel_mafii = random.sample( numerki_miastowych , 1)[0]  #losujemy tych z najwieksza iloscia glosow
    #print cel_mafii
    for x in range( len(kto_jest_kim)):
                   if kto_jest_kim[x] == 'm':
                       kto_na_kogo_glosowal[x] = cel_mafii
                       glosy_na_dana_osobe[ kto_na_kogo_glosowal[x] ] += 1 
                   elif kto_jest_kim[x] != 'd':  #a reszta glosuje jak zawsze
                        kto_na_kogo_glosowal[x]= kto_kogo_podejrzewa[x].argmax()
                        glosy_na_dana_osobe[ kto_na_kogo_glosowal[x] ] += 1
        # teraz bawimy sie remisem
    #print kto_na_kogo_glosowal
    max_glosow = max( glosy_na_dana_osobe )
    zwyciezcy = list( i for i in range( len( glosy_na_dana_osobe )) if glosy_na_dana_osobe[i] == max_glosow )
    ostatnio_zlinczowany = random.sample( zwyciezcy, 1 )[0]
    # a teraz outcome
    if kto_jest_kim[ ostatnio_zlinczowany ] == 'm':
        m += -1
    kto_jest_kim[ ostatnio_zlinczowany ] = 'd'
    return ( n - 1, m, ostatnio_zlinczowany )

def wykresuj_dla_jednego_mafiozo( n_min, n_max, ile_razy, **argumenty):    #funkcja robiaca wykresy
    lista=[]
    for n in range(n_min, n_max+1):
        lista.append(sum( list( kto_wygral_jedna_gre( n, 1, **argumenty) for i in range( ile_razy) ) ) / float( ile_razy ))  #tworzymy liste
    xlog =[i for i in range(n_min, n_max)]
    ylog=[lista[i] for i in range(0, len(lista)-1)]
    p.loglog(xlog, ylog, 'ro', color='blue')  #logarytmiczny wykres punktowy
    l=[]
    for x in range(0, len(lista), 2):
        l.append(math.log10(lista[x]))
    lis=[]
    for x in range(n_min, n_max+1, 2):
        lis.append(math.log10(x))
    a, b = najmniejsze(l, lis) #metoda najmniejszych kwadratow
    b=10**b
    ylog2=[(i**a)*b for i in range(n_min, n_max+1, 2)] #zadajemy prosta
    xlog2=[i for i in range(n_min, n_max+1, 2)]
    p.loglog(xlog2, ylog2, color='red')
    l=[]
    for x in range(1, len(lista), 2):
        l.append(math.log10(lista[x]))
    lis=[]
    for x in range(n_min+1, n_max+1, 2):
        lis.append(math.log10(x))
    c, d = najmniejsze(l, lis)
    d = 10**d
    ylog3=[(i**c)*d for i in range(n_min+1, n_max+1, 2)] #zadajemy prosta
    xlog3=[i for i in range(n_min+1, n_max+1, 2)]
    p.loglog(xlog3, ylog3, color='blue')
    p.show()  #pokazujemy wykres
    return lista

def najmniejsze(lista1, lista2):  #funkcja dzialajaca wg metody najmniejszych kwadratow, tak jak poprzednio wszystko
        assert len(lista1) == len(lista2), 'listy roznej dlugosci'
        c=sum(lista2)
        d=sum(lista1)
        e=sum(lista2[i]*lista1[i] for i in range(0, len(lista1)))
        f=sum(lista2[i]**2 for i in range(0, len(lista2)))
        a=(c*d-len(lista1)*e)/(c**2-len(lista1)*f)
        b=(c*e-d*f)/(c**2-len(lista1)*f)
        return a,b
