from django.conf.urls import url

from .views import log_in, authcode_send, signup, reset, preupload, getdatasets, \
    datasetsize, accesseddataset, getgpus, datasettype, gputype, prereserve, reserve, log_out, getroomsbygpuid, \
    getmaxmemory, roomadd, roomremove, getroombyroomid, roomedit, getroomsbymember, getaccessdata, getgpuipportbygpuid, \
    getrequestuser, clearlocation, getlocation, setlocation, getroomstatus, \
    getroomdata, getnickbyroomid, setnickname, getdatasetserveripport, getroomchataddr, deleteroom, getroomgradaddr

urlpatterns = [
    url(r'^login/$', log_in, name='login'),
    url(r'^logout/$', log_out, name='logout'),
    url(r'^signup/$', signup, name='signup'),
    url(r'^reset/$', reset, name='reset'),
    url(r'^preupload/$', preupload, name='preupload'),
    url(r'^getdatasetserveripport/$', getdatasetserveripport, name='getdatasetserveripport'),
    url(r'^getdatasets/$', getdatasets, name='getdatasets'),
    url(r'^getgpus/$', getgpus, name='getgpus'),
    url(r'^getroomsbygpuid/$', getroomsbygpuid, name='getroomsbygpuid'),
    url(r'^getroombyroomid/$', getroombyroomid, name='getroombyroomid'),
    url(r'^roomedit/$', roomedit, name='roomedit'),
    url(r'^getmaxmemory/$', getmaxmemory, name='getmaxmemory'),
    url(r'^getaccessdata/$', getaccessdata, name='getaccessdata'),
    url(r'^setnickname/$', setnickname, name='setnickname'),
    url(r'^getnickbyroomid/$', getnickbyroomid, name='getnickbyroomid'),
    url(r'^getroomdata/$', getroomdata, name='getroomdata'),
    url(r'^getgpuipportbygpuid/$', getgpuipportbygpuid, name='getgpuipportbygpuid'),
    url(r'^roomadd/$', roomadd, name='roomadd'),
    url(r'^getroomsbymember/$', getroomsbymember, name='getroomsbymember'),
    url(r'^roomremove/$', roomremove, name='roomremove'),
    url(r'^reserve/$', reserve, name='reserve'),
    url(r'^getrequestuser/$', getrequestuser, name='getrequestuser'),
    url(r'^datasettype/$', datasettype, name='datasettype'),
    url(r'^prereserve/$', prereserve, name='prereserve'),
    url(r'^gputype/$', gputype, name='gputype'),
    url(r'^datasetsize/$', datasetsize, name='datasetsize'),
    url(r'^accesseddataset/$', accesseddataset, name='accesseddataset'),
    url(r'^authcode_send/$', authcode_send, name='authcode_send'),
    url(r'^clearlocation/$', clearlocation, name='clearlocation'),
    url(r'^getlocation/$', getlocation, name='getlocation'),
    url(r'^setlocation/$', setlocation, name='setlocation'),
    url(r'^getroomstatus/$', getroomstatus, name='getroomstatus'),
    url(r'^getroomchataddr/$', getroomchataddr, name='getroomchataddr'),
    url(r'^getroomgradaddr/$', getroomgradaddr, name='getroomgradaddr'),
    url(r'^deleteroom/$', deleteroom, name='deleteroom'),
]
