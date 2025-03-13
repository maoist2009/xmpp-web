<template>
  <section class="hero is-fullheight">
    <div class="hero-body">
      <div class="container has-text-centered">
        <div class="column is-4 is-offset-4">
          <div class="box has-background-shade-3">
            <form @submit.prevent="login">
              <h3 class="title has-text-grey is-flex is-justify-content-center is-align-items-center"><img
                  class="image is-48x48 is-inline mr-2" :src="logoSrc">{{ appName }}</h3>
              <p class="subtitle has-text-grey">Login</p>
              <a href="/help.html">HELP</a>
              <div class="field">
                <div class="control has-icons-left">
                  <input v-model="credentials.jid" class="input is-medium" type="text" name="jid"
                    :placeholder="jidPlaceholder" @blur="onJidBlur">
                  <span class="icon is-small is-left">
                    <i class="fa fa-user" />
                  </span>
                  <div v-if="jidError" class="help is-danger">{{ jidError }}</div>
                </div>
              </div>
              <div class="field">
                <div class="control has-icons-left">
                  <input v-model="credentials.password" class="input is-medium" type="password" name="password"
                    placeholder="Password">
                  <span class="icon is-small is-left">
                    <i class="fa fa-lock" />
                  </span>
                </div>
              </div>
              <div class="field has-text-left pl-3">
                <o-checkbox v-model="credentials.remember" variant="primary" class="has-text-grey-light">
                  Store my password in browser
                </o-checkbox>
              </div>
              <o-collapse v-if="isTransportsUserAllowed" class="card has-background-shade-3 mb-3" :open="false"
                aria-id="connection-settings">
                <template #trigger="props">
                  <div role="button" aria-controls="connection-settings" class="card-header">
                    <p class="card-header-title has-text-grey-light"><span class="fa fa-cog fa-fw mr-3"
                        aria-hidden="true" />Connection settings</p>
                    <a class="card-header-icon has-text-grey-light">
                      <span class="fa fa-fw mr-3" :class="[props.open ? 'fa-caret-down' : 'fa-caret-up']"
                        aria-hidden="true" />
                    </a>
                  </div>
                </template>
                <div class="card-content">
                  <div class="field">
                    <div class="control">
                      <input v-model="transportsUser.websocket" class="input" type="url" name="websocket"
                        placeholder="wss://chat.domain.ltd/xmpp-websocket" title="Websocket url">
                    </div>
                  </div>
                </div>
              </o-collapse>
              <div class="field">
                <button type="submit" class="button is-block is-primary is-medium is-fullwidth"
                  :class="{ 'is-loading': isLoading }" :disabled="isDisabled"><span class="fa fa-sign-in fa-fw mr-3"
                    aria-hidden="true" />Login</button>
              </div>
              <div v-if="error" class="message is-danger">
                <div class="message-body has-text-danger">{{ error }}</div>
              </div>
            </form>
          </div>
        </div>
      </div>
    </div>
    <version />
  </section>
</template>

<script>
import { mapState } from 'pinia'
import { useStore } from '@/store'
import axios from 'axios'
import Version from '../components/Version.vue'

export default {
  name: 'Login',
  components: {
    Version,
  },
  data() {
    return {
      credentials: {
        jid: '',
        password: '',
        remember: false,
      },
      transportsUser: {
        websocket: window.config.transports.websocket,
      },
      isLoading: false,
      error: '',
      isTransportsUserAllowed: window.config.isTransportsUserAllowed,
      jidError: 'Please import your JID',
    }
  },
  computed: {
    isDisabled() {
      return this.isLoading || !this.credentials.jid || !this.credentials.password || !this.hasNetwork
    },
    jidPlaceholder() {
      return (typeof window.config.defaultDomain === 'string' && window.config.defaultDomain !== '') ? `username@${window.config.defaultDomain}` : 'username@domain.ltd'
    },
    appName() {
      return (typeof window.config.name === 'string' && window.config.name !== '') ? window.config.name : 'XMPP webchat'
    },
    logoSrc() {
      return window.config.logoUrl || 'img/icons/android-chrome-192x192.png'
    },
    ...mapState(useStore, ['hasNetwork']),
  },
  async mounted() {
    // remove navbar spacing
    document.body.classList.remove('has-navbar-fixed-top')
    // get auth by SSO
    if (window.config.sso && window.config.sso.endpoint && window.config.sso.jidHeader && window.config.sso.passwordHeader) {
      try {
        const ssoAuth = await axios.get(window.config.sso.endpoint)
        this.credentials.jid = ssoAuth.headers[window.config.sso.jidHeader]
        this.credentials.password = ssoAuth.headers[window.config.sso.passwordHeader]
        if (this.credentials.jid && this.credentials.password) {
          this.onJidBlur()
          this.login()
        }
      } catch (error) {
        console.warn(`SSO login failed (${error.message})`)
      }
    }
    // get stored credentials
    const jid = localStorage.getItem('jid')
    if (jid) {
      this.credentials.jid = jid
      this.onJidBlur()
    }
    const password = localStorage.getItem('p')
    if (password) {
      // auto login
      const reverse = (value) => value.split('').reverse().join('')
      this.credentials.password = reverse(atob(reverse(password)))
      this.login()
    }
  },
  methods: {
    async login() {
      this.error = ''
      const reverse = (value) => value.split('').reverse().join('')
      // check credentials are set
      if (this.credentials.jid === '' || this.credentials.password === '') {
        return
      }
      // call the auth service
      this.isLoading = true
      try {
        await this.$xmpp.create(this.credentials.jid, this.credentials.password, null, this.transportsUser, this)
        await this.$xmpp.connect()
        // authentication succeeded, route to requested page or default
        localStorage.setItem('jid',this.credentials.jid)
        if (this.credentials.remember) {
          localStorage.setItem('p', reverse(btoa(reverse(this.credentials.password))))
        }
        if (this.$route.query.redirect !== undefined) {
          return this.$router.push(this.$route.query.redirect)
        }
        this.$router.push('/')
      } catch (error) {
        // authentication failed, display error
        this.error = error.message
      }
      // remove loading status
      this.isLoading = false
    },
    onJidBlur() {
      // 检验用户名是否合法
      const jid = this.credentials.jid.trim()
      const domain = jid.split('@')[1]
      if (domain === undefined || domain === '') {
        this.jidError = 'Seems not to be a valid JID'
      }
      else {
        this.jidError = 'You may wait to auto get the wss url of the server'
        // 获取wss地址
        // 请求https://xxx.xx/.well-known/host-meta，使用fetch（可能有301 302等）
        fetch(`/xmppservers/${domain}`)
          .then(response => response.text())
          .then(xml => {
            const parser = new DOMParser();
            const xmlDoc = parser.parseFromString(xml, 'text/xml');
            const links = xmlDoc.getElementsByTagName('Link');
            for (let i = 0; i < links.length; i++) {
              const link = links[i];
              if (link.getAttribute('rel') === 'urn:xmpp:alt-connections:websocket') {
                this.transportsUser.websocket = link.getAttribute('href');
                this.jidError = '';
                break;
              }
            }
          })
          .catch(error => {
            console.error('Error getting host-meta', error);
            this.jidError = 'Failed to get the wss url of the server, you may specify it manually';
          });

        // 获取到的xml类似于这样
        /*
        <?xml version='1.0' encoding='utf-8'?>
        <XRD xmlns='http://docs.oasis-open.org/ns/xri/xrd-1.0'>
        <Link rel="urn:xmpp:alt-connections:xbosh"
          href="https://www.xmpp.jp/http-bind/" />
        <Link rel="urn:xmpp:alt-connections:websocket"
          href="wss://www.xmpp.jp/ws/" />
        </XRD>
        */
        // 解析xml获取wss地址，提取wss://www.xmpp.jp/ws/
        // 赋值给transportsUser.websocket
      }
    },
  },
}
</script>
