from rest_framework_nested import routers
from . import views


router = routers.DefaultRouter()

router.register('friends', views.UserFriendViewSet, basename='friend')
router.register('friend-request', views.FriendRequestViewSet, basename='friend-request')
router.register('friend-receive', views.FriendRequestDecisionViewSet, basename='friend-receive')
router.register('people', views.PeopleViewSet, basename='people')
router.register('posts', views.ListPostViewSet)
router.register('save', views.ListSavedPostViewSet, basename='saved-posts')

router.register('chat', views.ChatRoomViewSet, basename='chat')
router.register('group', views.GroupViewSet)

post_routes = routers.NestedDefaultRouter(router, 'posts', lookup='post')
post_routes.register('likes', views.LikePostViewSet, basename='post-likes')
post_routes.register('comments', views.CommentViewSet, basename='post-comments')
post_routes.register('save', views.SavePostViewSet, basename='save-post')

chat_routes = routers.NestedDefaultRouter(router, 'chat', lookup='chatroom')
chat_routes.register("messages", views.ChatMessagesViewSet, basename="chat-message")

group_routes = routers.NestedDefaultRouter(router, 'group', lookup='group')
group_routes.register('messages', views.GroupMessageViewSet, basename='group-message')
group_routes.register('members', views.GroupMemberViewSet, basename='group-members')

urlpatterns = router.urls + post_routes.urls + chat_routes.urls + group_routes.urls