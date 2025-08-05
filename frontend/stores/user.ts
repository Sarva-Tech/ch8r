import { USER_ID_PREFIX } from '~/lib/consts'

export interface User {
  id: number | null;
  email: string;
  username: string;
  name?: string | null;
  first_name?: string | null;
  last_name?: string | null;
}

export const useUserStore = defineStore('user', {
  state: () => ({
    authUser: {
      id: null,
      email: '',
      username: '',
      name: ''
    } as User,
  }),

  actions: {
    setUser(user: User) {
      this.authUser.id = user.id;
      this.authUser.email = user.email;
      this.authUser.username = user.username;
      this.authUser.name = [user?.first_name, user?.last_name].filter(Boolean).join(' ') || ''
    },
    clearUser() {
      this.authUser = { id: null, email: '', username: '', name: '' }
    },
  },

  getters: {
    isLoggedIn: (state) => !!state.authUser.id,
    getUser: (state) => state.authUser,
    getToken: () => useCookie('auth_token') || null,
    userIdentifier: (state) => `${USER_ID_PREFIX}_${state.authUser.id}`,
  },
});
