<?xml version="1.0" encoding="utf-8"?>
<gameSystem xmlns="http://www.battlescribe.net/schema/gameSystemSchema" id="a78e-11e0-40k0-0001" name="Warhammer 40,000 11e — Custom TEST" revision="1" battleScribeVersion="2.03" authorName="Custom 11e data test">
  <costTypes>
    <costType id="pts-11e0" name="pts" defaultCostLimit="-1" hidden="false"/>
  </costTypes>
  <profileTypes>
    <profileType id="stat-11e0" name="Unit">
      <characteristicTypes>
        <characteristicType id="m-11e0" name="M"/>
        <characteristicType id="t-11e0" name="T"/>
        <characteristicType id="sv-11e0" name="Sv"/>
        <characteristicType id="inv-11e0" name="Inv"/>
        <characteristicType id="w-11e0" name="W"/>
        <characteristicType id="ld-11e0" name="Ld"/>
        <characteristicType id="oc-11e0" name="OC"/>
      </characteristicTypes>
    </profileType>
    <profileType id="weapon-11e0" name="Weapon">
      <characteristicTypes>
        <characteristicType id="range-11e0" name="Range"/>
        <characteristicType id="attacks-11e0" name="A"/>
        <characteristicType id="skill-11e0" name="BS/WS"/>
        <characteristicType id="strength-11e0" name="S"/>
        <characteristicType id="ap-11e0" name="AP"/>
        <characteristicType id="damage-11e0" name="D"/>
      </characteristicTypes>
    </profileType>
  </profileTypes>
  <categoryEntries>
    <categoryEntry id="cat-units-11e0" name="Units" hidden="false"/>
  </categoryEntries>
  <forceEntries>
    <forceEntry id="force-11e0" name="Test Army" hidden="false">
      <categoryLinks>
        <categoryLink id="force-unit-link-11e0" name="Units" hidden="false" targetId="cat-units-11e0"/>
      </categoryLinks>
    </forceEntry>
  </forceEntries>
</gameSystem>
