Fy MySQL
--------
MySQL & Python shenanigans. Fy MySQL do not generate SQL tables it's just an util to simplify the relation between MySQL tables and python objects

**Schema example:**
  ```sql
  # Post
  CREATE TABLE `fypress_post` (
    `post_id` bigint(20) UNSIGNED NOT NULL,
    `post_user_id` bigint(20) UNSIGNED NOT NULL DEFAULT '0',
    `post_created` datetime NOT NULL DEFAULT '0000-00-00 00:00:00',
    `post_content` longtext COLLATE utf8mb4_unicode_ci NOT NULL,
    `post_title` text COLLATE utf8mb4_unicode_ci NOT NULL,
  ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
  
  
  ALTER TABLE `fypress_post`
    ADD PRIMARY KEY (`post_id`),
    ADD KEY `post_user_id` (`post_user_id`),
    ADD KEY `post_date` (`post_created`),
  
  ALTER TABLE `fypress_post`
    MODIFY `post_id` bigint(20) UNSIGNED NOT NULL AUTO_INCREMENT;  
    
  # User
  CREATE TABLE `fypress_user` (
    `user_id` bigint(20) UNSIGNED NOT NULL,
    `user_login` varchar(60) COLLATE utf8mb4_unicode_ci NOT NULL DEFAULT '',
    `user_password` varchar(255) COLLATE utf8mb4_unicode_ci NOT NULL DEFAULT '',
    `user_email` varchar(100) COLLATE utf8mb4_unicode_ci NOT NULL DEFAULT '',
  ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
  
  ALTER TABLE `fypress_user`
    ADD PRIMARY KEY (`user_id`),
    ADD UNIQUE KEY `user_email` (`user_email`),
    ADD UNIQUE KEY `user_login` (`user_login`),
    
  ALTER TABLE `fypress_user`
    MODIFY `user_id` bigint(20) UNSIGNED NOT NULL AUTO_INCREMENT;
    
  # User Meta
  CREATE TABLE `fypress_usermeta` (
    `usermeta_id_user` bigint(20) UNSIGNED NOT NULL DEFAULT '0',
    `usermeta_key` varchar(64) COLLATE utf8mb4_unicode_ci NOT NULL,
    `usermeta_value` longtext COLLATE utf8mb4_unicode_ci
  ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
  
  
  ALTER TABLE `fypress_usermeta`
    ADD PRIMARY KEY (`usermeta_id_user`,`usermeta_key`);

  ```
## Python Initiate Fy MySQL
  ```python
    import fy_mysql
    
    settings = {
        'user'              : 'fymysql',
        'passwd'            : 'pwd',
        'db'                : 'fymysql',
        'prefix'            : 'prefix_'
    }
    
    fy_mysql.db(**settings)
   ```
## Python User Class ##
  ```python
  class Post(mysql.Base):
      post_id               = mysql.Column(etype='int', primary_key=True)
      post_created          = mysql.Column(etype='datetime')
      post_content          = mysql.Column(etype='string')
      post_title            = mysql.Column(etype='string')
      post_user             = mysql.Column(object=User, link='user_id') 
  
  """
    post = Post.query.get(1)
    post.user is an User instance.
  """
  
  class UserMeta(mysql.Base):
      usermeta_id_user   = mysql.Column(etype='int', primary_key=True)
      usermeta_key       = mysql.Column(etype='string', primary_key=True)
      usermeta_value     = mysql.Column(etype='string')
      
  class User(mysql.Base):
      user_id                 = mysql.Column(etype='int', primary_key=True)
      user_login              = mysql.Column(etype='string', unique=True)
      user_email              = mysql.Column(etype='string', unique=True)
      user_password           = mysql.Column(etype='string')
      user_meta               = mysql.Column(obj=UserMeta, multiple='meta', link='usermeta_id_user')
  ```
## Examples ##
**GET User object with ID 1**
  ```python
    User.query.filter(id=1).one()
    # OR
    User.query.get(1)
  ```
**Get All Users**
  ```python
    User.query.get_all()
  ```
**Using Filters**
  ```python
    User.query.filter(email='test@fy.to'').one()
  ```
**Raw SQL**
  ```python
    # _table_ = current table, _fields_ all fields from _table_
    User.query.sql('SELECT * FROM _table_').all()
    User.query.sql('SELECT * FROM _table_').limit(0, 5)
  ```
**Insert / Update / Delete**
  ```python
    # insert
    u = User()
    u.login = 'mylogin'
    u.email = 'mymail@fy.to'
    u.meta  = {'url': 'http://mysite.fy.to', 'signature':'xxx'}
    User.query.add(u)
    u.dump() 
    
    # update
    u.meta['signature'] = 'bye!'
    User.query.update(u)
    u.dump()
     
    #delete
    User.query.delete(u)
  ```
## Soon ##
* Data cache
