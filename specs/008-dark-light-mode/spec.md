# Feature Specification: Dark/Light Mode pro Landing Page

**Feature Branch**: `008-dark-light-mode`
**Created**: 2026-03-17
**Status**: Draft
**Input**: Implementovat dark/light mode přepínač na landing page (apps/web). Aktuálně je stránka čistě dark s hardcoded barvami. Přidat theme toggle do navbaru a umožnit uživatelům přepínat mezi tmavým a světlým režimem.

## User Scenarios & Testing *(mandatory)*

### User Story 1 — Přepínání mezi tmavým a světlým režimem (Priority: P1)

Jako návštěvník landing page chci mít možnost přepnout na světlý režim, protože v jasném prostředí (kancelář, denní světlo) je tmavá stránka špatně čitelná a unavuje oči.

**Why this priority**: Přepínač je základní funkce celé feature — bez něj nemá smysl mít dvě barevné varianty.

**Independent Test**: Po implementaci může uživatel kliknout na ikonu v navbaru a celá stránka se okamžitě přepne na světlou/tmavou variantu.

**Acceptance Scenarios**:

1. **Given** uživatel vidí tmavou landing page (výchozí), **When** klikne na theme toggle ikonu v navbaru, **Then** celá stránka se přepne na světlý režim bez prodlevy a bez blikání
2. **Given** uživatel je ve světlém režimu, **When** klikne znovu na toggle, **Then** stránka se přepne zpět na tmavý režim
3. **Given** uživatel přepne na světlý režim, **When** stránku zavře a znovu otevře, **Then** stránka se zobrazí ve světlém režimu (volba se zachová)
4. **Given** uživatel nikdy nepřepínal režim, **When** jeho systém má nastavený světlý režim, **Then** stránka se zobrazí ve světlém režimu automaticky

---

### User Story 2 — Konzistentní světlá varianta všech sekcí (Priority: P1)

Jako návštěvník chci, aby ve světlém režimu byly všechny sekce stránky vizuálně konzistentní a čitelné, protože nekonzistentní barvy působí neprofesionálně.

**Why this priority**: Bez kompletní světlé varianty je přepínač nepoužitelný — částečně přepnutá stránka je horší než žádný přepínač.

**Independent Test**: Ve světlém režimu jsou všechny texty čitelné na světlém pozadí, všechny sekce mají harmonické barvy a žádný element není "rozbitý".

**Acceptance Scenarios**:

1. **Given** stránka je ve světlém režimu, **When** uživatel scrolluje celou stránkou, **Then** každá sekce (hero, features, problem-solution, tool-catalog, how-it-works, code-example, testimonial, CTA, footer) má konzistentní světlé barvy
2. **Given** stránka je ve světlém režimu, **When** uživatel čte text v jakékoli sekci, **Then** kontrastní poměr textu vůči pozadí splňuje WCAG AA standard (minimálně 4.5:1 pro normální text)
3. **Given** stránka je ve světlém režimu, **When** uživatel vidí terminálové ukázky kódu, **Then** kódové bloky mají tmavé pozadí (zůstávají dark) pro zachování čitelnosti a vizuální odlišnosti

---

### User Story 3 — Plynulý přechod bez blikání (Priority: P2)

Jako návštěvník chci, aby přechod mezi režimy byl plynulý a stránka při načtení neblikla, protože záblesk špatné barvy při načtení působí amatérsky.

**Why this priority**: Technický detail, ale výrazně ovlivňuje vnímanou kvalitu — "flash of unstyled content" je běžný problém theme přepínačů.

**Independent Test**: Při načtení stránky s uloženou preferencí se stránka zobrazí rovnou ve správném režimu bez viditelného záblesku.

**Acceptance Scenarios**:

1. **Given** uživatel má uloženu preferenci světlého režimu, **When** otevře stránku, **Then** stránka se vykreslí přímo ve světlém režimu bez viditelného tmavého záblesku
2. **Given** uživatel klikne na toggle, **When** stránka mění režim, **Then** přechod je plynulý (animace barev) bez skokové změny

---

### Edge Cases

- Co když uživatel má prefers-color-scheme: light ale ručně přepne na dark? Ruční volba MUSÍ přepsat systémovou preferenci
- Co když prohlížeč nepodporuje prefers-color-scheme? Výchozí režim je dark (zachování současného stavu)
- Co když uživatel má zapnutý Dark Reader nebo podobné rozšíření? Stránka NESMÍ kolidovat s rozšířeními prohlížeče
- Co když má mobilní zařízení malou obrazovku? Toggle MUSÍ být přístupný i na mobilním navbaru

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: Landing page MUSÍ nabízet přepínač dark/light režimu viditelný v navigačním panelu
- **FR-002**: Přepínač MUSÍ být přístupný i v mobilním menu
- **FR-003**: Výchozí režim MUSÍ respektovat systémovou preferenci uživatele (prefers-color-scheme)
- **FR-004**: Uživatelská volba MUSÍ být uložena a zachována mezi návštěvami
- **FR-005**: Ruční volba uživatele MUSÍ mít přednost před systémovou preferencí
- **FR-006**: Všech 11 komponent landing page MUSÍ mít funkční světlou variantu (hero, navbar, features, problem-solution, tool-catalog, how-it-works, code-example, testimonial, CTA, footer, fade-in)
- **FR-007**: Kódové bloky a terminálové ukázky MUSÍ zůstat ve tmavém stylu v obou režimech
- **FR-008**: Kontrastní poměr textu vůči pozadí MUSÍ splňovat WCAG AA standard (4.5:1 pro normální text)
- **FR-009**: Přechod mezi režimy NESMÍ způsobit viditelný záblesk špatné barvy při načtení stránky
- **FR-010**: Přepínač MUSÍ zobrazovat ikonu indikující aktuální stav (slunce pro světlý, měsíc pro tmavý)

### Assumptions

- Výchozí režim zůstává dark (zachování současného vizuálu jako výchozího)
- Dokumentace (apps/docs) má vlastní dark/light mode (Nextra) — tato feature se týká pouze landing page (apps/web)
- Gradient efekty a animace na pozadí hero sekce budou přizpůsobeny, ale nemusí být identické ve světlém režimu
- Barvy brandingu (modrá CzechMedMCP, zelená emerald) zůstanou konzistentní v obou režimech

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Uživatel může přepnout režim jedním kliknutím za méně než 0.3 sekundy
- **SC-002**: Při načtení stránky s uloženou preferencí se nezobrazí žádný viditelný záblesk jiného režimu
- **SC-003**: 100% sekcí stránky je vizuálně konzistentních ve světlém režimu (žádné hardcoded dark barvy)
- **SC-004**: Kontrastní poměr textu splňuje WCAG AA (4.5:1) ve všech sekcích v obou režimech
- **SC-005**: Volba režimu přežije zavření a znovuotevření prohlížeče
- **SC-006**: Stránka správně detekuje a respektuje systémovou preferenci při první návštěvě
