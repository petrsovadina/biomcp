"""Shared test fixtures for Czech healthcare module tests."""


SAMPLE_CLAML_XML = """\
<?xml version="1.0" encoding="UTF-8"?>
<ClaML version="2.0.0">
  <Title name="MKN-10" version="2018"/>
  <Class code="X" kind="chapter">
    <Rubric kind="preferred">
      <Label xml:lang="cs">Nemoci dýchací soustavy</Label>
    </Rubric>
    <SubClass code="J00-J06"/>
  </Class>
  <Class code="J00-J06" kind="block">
    <SuperClass code="X"/>
    <Rubric kind="preferred">
      <Label xml:lang="cs">\
Akutní infekce horních cest dýchacích</Label>
    </Rubric>
    <SubClass code="J06"/>
  </Class>
  <Class code="J06" kind="category">
    <SuperClass code="J00-J06"/>
    <Rubric kind="preferred">
      <Label xml:lang="cs">\
Akutní infekce horních cest dýchacích na více \
a neurčených místech</Label>
    </Rubric>
    <SubClass code="J06.9"/>
  </Class>
  <Class code="J06.9" kind="category">
    <SuperClass code="J06"/>
    <Rubric kind="preferred">
      <Label xml:lang="cs">\
Akutní infekce horních cest dýchacích NS</Label>
    </Rubric>
  </Class>
</ClaML>
"""
