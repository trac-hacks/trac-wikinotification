<?cs include "header.cs" ?>
<?cs include "macros.cs" ?>

<div id="content" class="notification"><p>
<?cs if notification.error ?>
  <h1>Notification Error</h1>
  <div class="system-message">
    <p>You must add your email address to
	<a href="<?cs var:settings.url ?>">Settings</a> in order to be able to
	use wiki notifications</p>
  </div>
<?cs else ?>
  <?cs if notification.showlist ?>
  <form id="notification" class="notification" method="post" style="float: right;" action="">
  <fieldset>
  <legend>Notification Settings</legend>
    <div class="field">
      <label>How many secconds should the redirect take?
      <input type="text" size="2" name="redirect_time" class="textwidget" value="<?cs var:notification.redirect_time ?>" /></label>
      <input name="update" value=" Update " type="submit">
    </div>
  </fieldset>
  </form>
    <?cs if:len(notification.list) >= 1 ?>
	  <p>&nbsp<p>
      <h1>List of Watched Pages</h1>
      <form method="post">
        <table class="listing" id="watched_pages_list">
          <thead>
            <tr><th class="sel">&nbsp;</th><th>Watched Wiki Pages</th></tr>
          </thead><tbody><?cs
          each: page = notification.list ?>
          <tr>
            <td><input type="checkbox" name="sel" value="<?cs var:page ?>" /></td>
            <td width="100%"><a href="<?cs var:notification.wikiurl ?>/<?cs var:page ?>"><?cs var:page ?></td>
          </tr><?cs
          /each ?></tbody>
        </table>
        <div class="buttons">
          <input type="submit" name="remove" value="Stop watching selected wiki pages" />
        </div>
      </form>
    <?cs else ?>
      <p>&nbsp<p>
      <h1>You are not watching any wiki pages</h1>
    <?cs /if ?>
  <?cs else ?>
  <script language="JavaScript">
  function redirectBack() {
      redirurl = "<?cs var:notification.redir ?>";
      redirect_time = <?cs var:notification.redirect_time ?>*1000;
      self.setTimeout("self.location.href = redirurl;", redirect_time);
  }
  </script>
  <p>
  <fieldset>
    <legend><?cs var:notification.action ?> <?cs var:notification.wikipage ?></legend>
    <?cs if:notification.action == 'watch' ?>
      <h1>You will now recieve emails about changes made on
      <a href="<?cs var:notification.wikipage.url ?>">
      <?cs var:notification.wikipage ?></a>.</h1>
    <?cs else ?>
      <h1>No more emails about changes made on
      <?cs if:len(notification.removelist) == 1 ?>
      <?cs each: item=notification.removelist ?>
        <a href="<?cs var:notification.wikiurl ?>/<?cs var:item ?>"><?cs var:item ?></a>
        <?cs /each ?>
      <?cs elif:len(notification.removelist) > 1 ?>
        <?cs each: item=notification.removelist ?>
          <a href="<?cs var:notification.wikiurl ?>/<?cs var:item ?>"><?cs var:item ?></a>,
        <?cs /each ?>
      <?cs else ?>
        <a href="<?cs var:notification.wikiurl ?>/<?cs var:notification.wikipage ?>">
        <?cs var:notification.wikipage ?></a>
      <?cs /if ?>
        will be sent to you.</h1>
    <?cs /if ?>

  <p>Redirecting you back, if it fails, please
  <a href="<?cs var:notification.redir ?>">click here</a></p>

  <p>A list of the wiki pages you're watching can be found on
  <a href="<?cs var:notification.my_not_url ?>">My Notifications</a>.</p>
  </fieldset>
  <p>

  <script type="text/javascript">redirectBack();</script>

  <?cs /if ?>
<?cs /if ?>
</div>

<?cs include "footer.cs" ?>
