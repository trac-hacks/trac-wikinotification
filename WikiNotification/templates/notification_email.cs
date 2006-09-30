<?cs if:action == 'added' ?>
Added page "<?cs var:name ?>" by <?cs var:author ?> from <?cs var:ip ?>
Page URL: <<?cs var:link ?>>
Comment: <?cs var:comment ?>
Content:

<?cs var:text ?>

<?cs elif:action == 'modified' ?>

Changed page "<?cs var:name ?>" by <?cs var:author ?> from <?cs var:ip ?>
Page URL: <<?cs var:link ?>>
Diff URL: <<?cs var:linkdiff ?>>
Revision <?cs var:version ?> 
Comment: <?cs var:comment ?>

Changes on attached <?cs var:name ?>.diff file.
  
<?cs elif:action == 'deleted' ?>
Deleted page "<?cs var:name ?>" by <?cs var:author ?> from <?cs var:ip ?>

<?cs elif:action == 'deleted_version' ?>
Page URL: <<?cs var:link ?>>
Deleted version "<?cs var:version ?>" of page "<?cs var:name ?>" by  <?cs var:author ?> from <?cs var:ip ?>

<?cs /if ?>
-- 
<?cs var:project.name ?> <<?cs var:project.url ?>>
<?cs var:project.descr ?>
