Name:           coturn
Version:        4.5.1.0
Release:        1%{?dist}
Summary:        TURN/STUN & ICE Server
License:        BSD
URL:            https://github.com/coturn/coturn/
Source0:        https://github.com/coturn/coturn/archive/%{version}/%{name}-%{version}.tar.gz
Source1:        coturn.service

BuildRequires:  gcc
BuildRequires:  hiredis-devel
BuildRequires:  libevent-devel >= 2.0.0
BuildRequires:  make
BuildRequires:  mariadb-devel
BuildRequires:  openssl-devel
BuildRequires:  postgresql-devel
BuildRequires:  sqlite-devel
BuildRequires:  systemd
Requires(pre): shadow-utils
Requires:       hiredis
Requires:       libevent >= 2.0.0
Requires:       openssl
Requires:       perl-DBI
Requires:       perl-libwww-perl
Requires:       telnet
Provides:       turnserver = %{version}
%{?systemd_requires}

%description
The Coturn TURN Server is a VoIP media traffic NAT traversal server and gateway.
It can be used as a general-purpose network traffic TURN server/gateway, too.

This implementation also includes some extra features. Supported RFCs:

TURN specs:
- RFC 5766 - base TURN specs
- RFC 6062 - TCP relaying TURN extension
- RFC 6156 - IPv6 extension for TURN
- Experimental DTLS support as client protocol.

STUN specs:
- RFC 3489 - "classic" STUN
- RFC 5389 - base "new" STUN specs
- RFC 5769 - test vectors for STUN protocol testing
- RFC 5780 - NAT behavior discovery support

The implementation fully supports the following client-to-TURN-server protocols:
- UDP (per RFC 5766)
- TCP (per RFC 5766 and RFC 6062)
- TLS (per RFC 5766 and RFC 6062); TLS1.0/TLS1.1/TLS1.2
- DTLS (experimental non-standard feature)

Supported relay protocols:
- UDP (per RFC 5766)
- TCP (per RFC 6062)

Supported user databases (for user repository, with passwords or keys, if
authentication is required):
- SQLite
- MySQL
- PostgreSQL
- Redis

Redis can also be used for status and statistics storage and notification.

Supported TURN authentication mechanisms:
- long-term
- TURN REST API (a modification of the long-term mechanism, for time-limited
  secret-based authentication, for WebRTC applications)

The load balancing can be implemented with the following tools (either one or a
combination of them):
- network load-balancer server
- DNS-based load balancing
- built-in ALTERNATE-SERVER mechanism.


%package        utils
Summary:        Coturn utils
%description    utils
This package contains the TURN client utils.


%package        client-libs
Summary:        TURN client library
Requires:       openssl
Requires:       libevent >= 2.0.0
%description    client-libs
This package contains the TURN client library.


%package        client-devel
Summary:        Coturn client development headers
Requires:       openssl
Requires:       libevent >= 2.0.0
%description    client-devel
This package contains the TURN client development headers.


%prep
%setup -q -n %{name}-%{version}
# NOTE: Use Fedora Default Ciphers
sed -i \
    -e 's/#define DEFAULT_CIPHER_LIST "DEFAULT"/#define DEFAULT_CIPHER_LIST "PROFILE=SYSTEM"/g' \
    -e 's/\/* "ALL:eNULL:aNULL:NULL" *\//\/* Fedora Defaults *\//g' \
    src/apps/relay/mainrelay.h
sed -i \
    -e 's/*csuite = "ALL"; \/\/"AES256-SHA" "DH"/*csuite = "PROFILE=SYSTEM"; \/\/ Fedora Defaults/g' \
    src/apps/uclient/mainuclient.c


%build
%configure --confdir=%{_sysconfdir}/%{name} \
    --examplesdir=%{_docdir}/%{name} \
    --schemadir=%{_datadir}/%{name} \
    --manprefix=%{_datadir} \
    --docdir=%{_docdir}/%{name} \
    --disable-rpath
%make_build


%pre
getent group coturn >/dev/null || groupadd -r coturn
getent passwd coturn >/dev/null || \
    useradd -r -g coturn -d %{_datadir}/%{name} -s /sbin/nologin \
    -c "Coturn TURN Server daemon" coturn
exit 0


%check
make test


%install
%make_install
mkdir -p %{buildroot}%{_sysconfdir}/pki/coturn/{public,private}
install -Dpm 0644 %{SOURCE1} %{buildroot}%{_unitdir}/coturn.service
sed -i \
    -e "s/^syslog$/#syslog/g" \
    -e "s/cert=\/etc\/ssl\/certs\/cert.pem/#cert=\/etc\/pki\/coturn\/public\/turn_server_cert.pem/g" \
    -e "s/pkey=\/etc\/ssl\/private\/privkey.pem/#pkey=\/etc\/pki\/coturn\/private\/turn_server_pkey.pem/g" \
    %{buildroot}%{_sysconfdir}/%{name}/turnserver.conf.default
mv %{buildroot}%{_sysconfdir}/%{name}/turnserver.conf.default %{buildroot}%{_sysconfdir}/%{name}/turnserver.conf
# NOTE: Removing sqlite db, certs and keys
rm -rf %{buildroot}%{_localstatedir}/db
rm %{buildroot}%{_docdir}/%{name}/etc/turn_client_cert.pem
rm %{buildroot}%{_docdir}/%{name}/etc/turn_client_pkey.pem
rm %{buildroot}%{_docdir}/%{name}/etc/turn_server_cert.pem
rm %{buildroot}%{_docdir}/%{name}/etc/turn_server_pkey.pem


%post
%systemd_post coturn.service


%preun
%systemd_preun coturn.service


%postun
%systemd_postun_with_restart coturn.service


%files
%license %{_docdir}/%{name}/LICENSE
%{_bindir}/turnserver
%{_bindir}/turnadmin
%dir %{_datadir}/%{name}
%{_datadir}/%{name}/*.redis
%{_datadir}/%{name}/*.sql
%{_datadir}/%{name}/*.sh
%dir %{_docdir}/%{name}
%{_docdir}/%{name}/README.*
%exclude %{_docdir}/%{name}/README.turnutils
%exclude %{_docdir}/%{name}/INSTALL
%exclude %{_docdir}/%{name}/LICENSE
%exclude %{_docdir}/%{name}/postinstall.txt
%dir %{_docdir}/%{name}/etc
%doc %{_docdir}/%{name}/etc/*
%dir %{_docdir}/%{name}/scripts
%dir %{_docdir}/%{name}/scripts/*
%{_docdir}/%{name}/scripts/*.sh
%{_docdir}/%{name}/scripts/readme.txt
%doc %{_docdir}/%{name}/scripts/*/*
# NOTE: These schema files are installed twice. Excluding copies in docs.
%exclude %doc %{_docdir}/%{name}/schema.mongo.sh
%exclude %doc %{_docdir}/%{name}/schema.sql
%exclude %doc %{_docdir}/%{name}/schema.stats.redis
%exclude %doc %{_docdir}/%{name}/schema.userdb.redis
%{_mandir}/man1/coturn.1.*
%{_mandir}/man1/turnserver.1.*
%{_mandir}/man1/turnadmin.1.*
%dir %{_sysconfdir}/%{name}
%config(noreplace) %{_sysconfdir}/%{name}/turnserver.conf
%{_sysconfdir}/pki/coturn
%{_unitdir}/coturn.service


%files utils
%{_bindir}/turnutils_peer
%{_bindir}/turnutils_stunclient
%{_bindir}/turnutils_uclient
%{_bindir}/turnutils_oauth
%{_bindir}/turnutils_natdiscovery
%doc %{_docdir}/%{name}/README.turnutils
%{_mandir}/man1/turnutils.1.*
%{_mandir}/man1/turnutils_*.1.*


%files client-libs
%{_docdir}/%{name}/LICENSE
%{_libdir}/libturnclient.a


%files client-devel
%dir %{_includedir}/turn
%{_includedir}/turn/*.h
%dir %{_includedir}/turn/client
%{_includedir}/turn/client/*


%changelog
* Mon Feb 18 2019 Christian Glombek <lorbus@fedoraproject.org> - 4.5.1.0-1
- Initial Fedora Package
- Update to 4.5.1.0
- Introduce consistent naming, rename service to coturn
- Add configure, make and systemd macros
- Remove dependencies on mariadb, mysql, postgresql and sqlite
- Forked from https://github.com/coturn/coturn/blob/af674368d120361603342ff4ff30b44f147a38ff/rpm/turnserver.spec
