<?xml version="1.0" encoding="utf-8"?>
<gameSystem xmlns="http://www.battlescribe.net/schema/gameSystemSchema" id="a78e-11e0-40k0-0001" name="Warhammer 40,000 11e — Custom TEST" revision="1" battleScribeVersion="2.03" authorName="Custom 11e data test">
  <costTypes>
    <costType id="pts-11e0" name="pts" defaultCostLimit="-1" hidden="false"/>
  </costTypes>
  <profileTypes>
    <profileType id="stat-11e0" name="Units">
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
    <profileType id="fd-ranged-type" name="Ranged Weapons">
      <characteristicTypes>
        <characteristicType id="fd-rng" name="Range"/>
        <characteristicType id="fd-rna" name="A"/>
        <characteristicType id="fd-rbs" name="BS"/>
        <characteristicType id="fd-rs" name="S"/>
        <characteristicType id="fd-rap" name="AP"/>
        <characteristicType id="fd-rd" name="D"/>
        <characteristicType id="fd-rkw" name="Keywords"/>
      </characteristicTypes>
    </profileType>
    <profileType id="fd-melee-type" name="Melee Weapons">
      <characteristicTypes>
        <characteristicType id="fd-mrng" name="Range"/>
        <characteristicType id="fd-ma" name="A"/>
        <characteristicType id="fd-mws" name="WS"/>
        <characteristicType id="fd-ms" name="S"/>
        <characteristicType id="fd-map" name="AP"/>
        <characteristicType id="fd-md" name="D"/>
        <characteristicType id="fd-mkw" name="Keywords"/>
      </characteristicTypes>
    </profileType>
    <profileType id="ability-11e0" name="Abilities">
      <characteristicTypes><characteristicType id="description-11e0" name="Description"/></characteristicTypes>
    </profileType>
    <profileType id="fd-rule-type" name="Rules">
      <characteristicTypes><characteristicType id="fd-rule-description" name="Description"/></characteristicTypes>
    </profileType>
    <profileType id="keywords-11e0" name="Keywords">
      <characteristicTypes>
        <characteristicType id="unit-keywords-11e0" name="Keywords"/>
        <characteristicType id="faction-keywords-11e0" name="Faction Keywords"/>
      </characteristicTypes>
    </profileType>
  </profileTypes>
  <categoryEntries>
    <categoryEntry id="cat-units-11e0" name="Units" hidden="false"/>
    <categoryEntry id="cat-infantry-11e0" name="Infantry" hidden="false"/>
    <categoryEntry id="cat-aeldari-11e0" name="Aeldari" hidden="false"/>
    <categoryEntry id="cat-rangers-11e0" name="Rangers" hidden="false"/>
    <categoryEntry id="cat-asuryani-11e0" name="Asuryani" hidden="false"/>
    <categoryEntry id="cat-ynnari-11e0" name="Ynnari" hidden="false"/>
    <categoryEntry id="fd-category-0" name="Grenades" hidden="false"/>
    <categoryEntry id="fd-category-1" name="Fire Dragons" hidden="false"/>
    <categoryEntry id="fd-category-2" name="Aspect Warriors" hidden="false"/>
  </categoryEntries>
  <forceEntries>
    <forceEntry id="force-11e0" name="Test Army" hidden="false">
      <categoryLinks>
        <categoryLink id="force-infantry-link-11e0" name="Infantry" hidden="false" targetId="cat-infantry-11e0"/>
      </categoryLinks>
    </forceEntry>
  </forceEntries>
</gameSystem>
