from docx import Document
from docx.shared import Inches, Pt, RGBColor
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.enum.table import WD_TABLE_ALIGNMENT, WD_CELL_VERTICAL_ALIGNMENT
from pathlib import Path

ROOT=Path(__file__).parent
doc=Document()
sec=doc.sections[0]
sec.top_margin=sec.bottom_margin=Inches(.65)
sec.left_margin=sec.right_margin=Inches(.65)
sec.page_width=Inches(8.27); sec.page_height=Inches(11.69)
for name in ['Normal','Title','Heading 1','Heading 2']:
 s=doc.styles[name]; s.font.name='Calibri'; s.font.color.rgb=RGBColor(0,0,0)
doc.styles['Normal'].font.size=Pt(10)
doc.styles['Normal'].paragraph_format.space_after=Pt(6)
doc.styles['Title'].font.size=Pt(25)
doc.styles['Heading 1'].font.size=Pt(17)
doc.styles['Heading 2'].font.size=Pt(12)

def p(t): doc.add_paragraph(t)
def h(t): doc.add_heading(t,1)
def table(headers, rows, widths):
 t=doc.add_table(rows=1, cols=len(headers)); t.alignment=WD_TABLE_ALIGNMENT.CENTER; t.autofit=False
 for c,w in zip(t.columns,widths): c.width=Inches(w)
 for c,v in zip(t.rows[0].cells,headers): c.text=v
 for row in rows:
  for c,v in zip(t.add_row().cells,row): c.text=v
 for i,row in enumerate(t.rows):
  for j,c in enumerate(row.cells):
   c.width=Inches(widths[j]); c.vertical_alignment=WD_CELL_VERTICAL_ALIGNMENT.CENTER
   pr=c._tc.get_or_add_tcPr()
   bd=OxmlElement('w:tcBorders')
   for edge in ['top','left','bottom','right']:
    e=OxmlElement('w:'+edge); e.set(qn('w:val'),'single'); e.set(qn('w:sz'),'4'); e.set(qn('w:color'),'D9D9D9'); bd.append(e)
   pr.append(bd)
   mar=OxmlElement('w:tcMar')
   for edge in ['top','left','bottom','right']:
    e=OxmlElement('w:'+edge); e.set(qn('w:w'),'90'); e.set(qn('w:type'),'dxa'); mar.append(e)
   pr.append(mar)
   shade=OxmlElement('w:shd'); shade.set(qn('w:fill'),'E7EEF5' if i==0 else ('F5F5F5' if i%2==0 else 'FFFFFF')); pr.append(shade)
   for para in c.paragraphs:
    para.paragraph_format.space_after=Pt(2)
    para.paragraph_format.space_before=Pt(2)
    for r in para.runs: r.font.size=Pt(9); r.bold=i==0
  rr=OxmlElement('w:cantSplit'); row._tr.get_or_add_trPr().append(rr)
 repeat=OxmlElement('w:tblHeader'); t.rows[0]._tr.get_or_add_trPr().append(repeat)
 doc.add_paragraph().paragraph_format.space_after=Pt(0)
 return t

doc.add_paragraph('YouTube Audio Story Website Project Tracker','Title')
p('Updated 4 October 2026 | Version 2 | Project stage: planning')
p('We are building a mobile-friendly website that recommends YouTube audio stories based on a listener’s taste and current need. This tracker breaks the work into small steps, with progress shown beside every step. The website has not been implemented yet.')
h('Agreed direction')
p('Start with a website. Collect favorite story links and explicit feedback, recommend a few suitable stories, and provide a route to YouTube playback. Treat the recommendation process as small problems with clear inputs and outputs.')
p('Proposed first-version architecture: Cloudflare Pages hosts the website and curated catalog. The browser filters and ranks stories and saves preferences and feedback locally. AI enriches the catalog during preparation; live AI calls are deferred. Hosting setup and AI processing costs must be checked before implementation.')
h('Overall progress')
table(['Milestone','Completed steps','Progress'],[
 ('A Define listener needs','0 / 4','0% | Not started'),('B Prepare and enrich the catalog','0 / 7','0% | Not started'),('C Define recommendation rules','0 / 4','0% | Not started'),('D Build the first website','0 / 6','0% | Not started'),('E Validate and release','0 / 4','0% | Not started')],[3.35,1.25,2.37])
p('Implementation checklist: 0 of 25 steps complete. Product direction is agreed; the executable steps below remain open. Percent complete = completed steps / total steps × 100. This counts deliverables, not effort or time.')
h('How to maintain the tracker')
p('Replace each status with Not started, In progress, Blocked, or Done. Mark Done only when the completion evidence exists. Update milestone counts and percentages after each work session. Assign owners and dates before starting; neither is committed yet.')
p('First action: choose the initial language and listener group, then record three examples of the listening problem.')

doc.add_page_break()
h('A Define listener needs')
p('Small problem: what minimum information lets us make a useful first recommendation? Output: an agreed listener profile and first-version scope.')
table(['ID','Small step and completion evidence','Progress'],[
 ('A1','Choose one initial language and listener group. Done when both are recorded in the decision log.','Not started'),
 ('A2','Collect three listening situations and the difficulty in each. Done when concrete examples are written.','Not started'),
 ('A3','Choose the starting questions: favorite links, genre, narrator preferences, mood and duration. Done when the minimum fields are agreed.','Not started'),
 ('A4','Approve the first-version scope and exclusions. Done when the core user journey and success criteria are recorded.','Not started')],[.45,5.15,1.37])
h('B Prepare the story catalog')
p('Small problem: what do we need to know about each story to compare it fairly? Output: a small, usable catalog with consistent attributes.')
table(['ID','Small step and completion evidence','Progress'],[
 ('B1','Define story fields: video link, title, language, genre, narrator, duration, mood, series order and content labels. Done when a sample record is complete.','Not started'),
 ('B2','Investigate permitted YouTube discovery and playback options, API access and quotas. Done when the chosen approach and constraints are documented.','Not started'),
 ('B3','Curate an initial catalog. Proposed target: 30 stories in the chosen language. Done when links and essential fields are checked.','Not started'),
 ('B4','Define missing-data and unavailable-video handling. Done when incomplete records and broken links have a clear treatment.','Not started')],[.45,5.15,1.37])
p('Dependency: A1 before catalog selection; B1 and B2 before B3. Catalog size is a proposed starting target, not an agreed commitment.')

doc.add_page_break()
h('AI role in the first version')
p('AI works during catalog preparation. It turns available descriptions or permitted transcripts into structured tags for themes, setting, mood and storytelling style. A person reviews those tags before they enter the website catalog. The browser then uses ordinary scoring code to recommend verified stories.')
p('Flow: story information → AI tagging → human review → enriched catalog → browser filters and ranking → three recommendations → YouTube playback. Explicit listener feedback updates the local taste profile and later rankings.')
table(['ID','Small step and completion evidence','Progress'],[
 ('B5','Define the AI tagging schema and input sources. Done when a sample includes themes, setting, mood, source evidence and unknown fields, and an AI tool and cost approach are chosen.','Not started'),
 ('B6','Tag the initial catalog with AI and review every record. Done when supported tags are approved, unsupported claims removed, and original links retained.','Not started'),
 ('B7','Export the reviewed catalog as a website data file. Done when each video ID is unique and the browser can load validated tags without live AI calls.','Not started')],[.45,5.15,1.37])
h('Evidence and controls')
p('AI must use the supplied story information and preserve verified video IDs. Unknown attributes stay unknown. Voice quality, narration pace and background music require audio evidence or human review; text descriptions alone do not establish them. Recommendation explanations use saved matching attributes rather than invented facts or links.')
h('Future live AI option')
p('A later version could interpret requests such as “something like yesterday’s story, but less frightening.” Proposed flow: browser → backend → AI service → validated catalog candidates → strict filters → recommendations. This is deferred work and is excluded from the 25-step first-version checklist.')
p('Before adding live AI, decide the provider, budget, backend, consent and data handling. Keep API credentials on the backend. Free website hosting does not make AI processing free. The first version needs no per-visit AI request or paid database; local data does not sync across devices.')
p('Dependencies: B1, B2 and B3 before B5; B5 before B6; B4 and B6 before B7; B7 before C3 and D4. The first AI experiment uses the proposed 30-story catalog and three example listener profiles.')

doc.add_page_break()
h('C Define recommendation rules')
p('Small problem: which eligible stories best fit this listener today? Output: explainable ranking rules that can be checked before building the interface.')
table(['ID','Small step and completion evidence','Progress'],[
 ('C1','Define hard filters such as language, maximum duration, hidden channels and already-heard stories. Done when each filter has an example.','Not started'),
 ('C2','Define browser scoring over reviewed AI tags using taste, current need and discovery value. Done when weights, missing-data rules and attribute-based explanations are recorded.','Not started'),
 ('C3','Try three listener profiles against the enriched catalog. Done when each receives three verified, eligible suggestions with reasons and differences from genre-only matching are reviewed.','Not started'),
 ('C4','Define feedback updates and a fallback for sparse matches. Done when likes, dislikes and already-heard feedback produce expected changes.','Not started')],[.45,5.15,1.37])
p('Initial scoring model: score = weighted taste match + weighted current-need match + weighted discovery value. Apply hard filters first. Include audio quality only if the catalog contains reliable quality information. Weights remain to be decided.')
h('D Build the first website')
table(['ID','Small step and completion evidence','Progress'],[
 ('D1','Design the homepage using Homepage Content.md: problem, vision, planned monetization and discovery actions. Sketch preferences, recommendations, details and queue. Done when the content and complete mobile journey are reviewable.','Not started'),
 ('D2','Choose the stack and implement catalog loading and browser local storage. Done when setup runs and Cloudflare Pages deployment requirements are checked.','Not started'),
 ('D3','Build preference and favorite-link input. Done when valid inputs save and invalid links receive clear feedback.','Not started'),
 ('D4','Build filtered recommendation cards with reasons. Done when catalog data and ranking rules produce usable results.','Not started'),
 ('D5','Add YouTube playback or open-on-YouTube links. Done when available and unavailable videos behave as intended.','Not started'),
 ('D6','Add feedback, saved queue and preference reset. Done when actions persist and affect later recommendations.','Not started')],[.45,5.15,1.37])
p('Dependency: catalog and baseline rules before D4; playback feasibility before D5. Login, automated listening-history import, background playback, downloads and a native app are deferred pending need and feasibility.')

doc.add_page_break()
h('E Validate and release')
table(['ID','Small step and completion evidence','Progress'],[
 ('E1','Check phone, desktop and keyboard use; verify hard filters, reviewed tags, explanations, empty matches, broken videos and preference reset. Done when critical issues are resolved.','Not started'),
 ('E2','Run a small listener trial. Proposed: five listeners, each reviewing three suggestions. Done when choices, ratings and comments are recorded.','Not started'),
 ('E3','Review results and improve weak recommendations. Done when the release criteria are met or remaining issues are explicitly accepted.','Not started'),
 ('E4','Prepare a reviewable release, privacy text and deployment instructions. Done when the website is released after approval and a smoke check passes.','Not started')],[.45,5.15,1.37])
p('Proposed trial criteria: no hard-filter violations; at least four of five listeners find one of their top three suggestions worth listening to; median time from opening recommendations to choosing a story is under two minutes. Agree or revise these targets in A4. A playback click is not evidence that a story was enjoyed.')
h('Open decisions')
table(['Decision','Current position','Resolve by'],[
 ('Initial language and audience','To be decided','A1'),('Catalog source and YouTube integration','Research required','B2'),('AI tagging tool and preparation cost','To be decided; human review required','B5'),('Recommendation weights','To be decided','C2'),('Hosting and storage','Proposed Cloudflare Pages and browser local storage; stack remains open','D2'),('Live AI service','Deferred beyond first version','Future review'),('Owners and target dates','Unassigned and unscheduled','Before each milestone')],[2.35,3.25,1.37])
h('Blockers and next actions')
table(['Issue','Next action','Status'],[
 ('Audience is not selected','Complete A1','Open'),('YouTube capabilities are unverified','Complete B2 before promising integration features','Open')],[2.35,3.25,1.37])
h('Work session log')
table(['Date','Steps changed and evidence','Next action'],[
 ('4 Oct 2026','Version 1 created; website direction captured.','A1'),('4 Oct 2026','Version 2 adds AI tagging, human review and catalog export; browser ranking and proposed hosting clarified. 0 of 25 steps complete.','A1 then B5 after prerequisites'),('To fill','Record IDs, new status, evidence and blockers.','To fill')],[1.05,4.55,1.37])
doc.core_properties.title='YouTube Audio Story Website Project Tracker'
doc.core_properties.subject='Small steps and side by side progress tracking'
doc.save(ROOT/'Project Tracker.docx')
