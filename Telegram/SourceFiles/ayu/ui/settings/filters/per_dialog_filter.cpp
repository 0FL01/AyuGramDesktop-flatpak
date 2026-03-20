// This is the source code of AyuGram for Desktop.
//
// We do not and cannot prevent the use of our code,
// but be respectful and credit the original author.
//
// Copyright @Radolyn, 2025
#include "per_dialog_filter.h"

#include <utility>

#include "lang_auto.h"
#include "settings_filters_list.h"
#include "ayu/ayu_settings.h"
#include "ayu/data/ayu_database.h"
#include "ayu/features/filters/shadow_ban_utils.h"
#include "ayu/utils/telegram_helpers.h"
#include "data/data_peer.h"
#include "data/data_session.h"
#include "main/main_session.h"
#include "styles/style_menu_icons.h"
#include "ui/painter.h"
#include "window/window_session_controller.h"

namespace Settings {

PerDialogFiltersListRow::PerDialogFiltersListRow(PeerId peer)
	: PeerListRow(peer.value)
	  , peerId(peer) {
}

QString PerDialogFiltersListRow::generateName() {
	if (const auto from = getPeerFromDialogId(peerId.value & PeerId::kChatTypeMask)) {
		this->setPeer(from);
		return PeerListRow::generateName();
	}
	return QString("UNKNOWN (ID: %1)").arg(QString::number(peerId.value & PeerId::kChatTypeMask));
}

PaintRoundImageCallback PerDialogFiltersListRow::generatePaintUserpicCallback(bool forceRound) {
	if (const auto from = getPeerFromDialogId(peerId.value & PeerId::kChatTypeMask)) {
		this->setPeer(from);
		return PeerListRow::generatePaintUserpicCallback(forceRound);
	}

	return [=](Painter &p, int x, int y, int outerWidth, int size) mutable
	{
		using namespace Ui;
		const auto realId = peerId.value & PeerId::kChatTypeMask;
		auto _userpicEmpty = std::make_unique<EmptyUserpic>(
			EmptyUserpic::UserpicColor(realId % 7),
			QString("U")); // U - Unknown
		_userpicEmpty->paintCircle(p, x, y, outerWidth, size);
	};
}

PerDialogFiltersListController::PerDialogFiltersListController(not_null<Main::Session*> session,
															   not_null<Window::SessionController*> controller,
															   bool shadowBan)
	: _session(session)
	  , _controller(controller)
	  , shadowBan(shadowBan) {
}

Main::Session &PerDialogFiltersListController::session() const {
	return *_session;
}

void PerDialogFiltersListController::prepareShadowBan() {
	const auto &settings = AyuSettings::getInstance();
	const auto &shadowBanned = settings.shadowBanIds;

	for (const auto id : shadowBanned) {
		auto peerId = PeerId(PeerIdHelper(abs(id)));

		auto row = std::make_unique<PerDialogFiltersListRow>(peerId);

		delegate()->peerListAppendRow(reinterpret_cast<std::unique_ptr<PeerListRow>&&>(row));
	}
}

void PerDialogFiltersListController::prepare() {
	if (shadowBan) {
		prepareShadowBan();
		return;
	}
	const auto filters = AyuDatabase::getAllRegexFilters();
	const auto exclusions = AyuDatabase::getAllFiltersExclusions();

	if (filters.empty() && exclusions.empty()) {
		return;
	}

	countsByDialogIds.clear();

	for (const auto &filter : filters) {
		if (filter.dialogId.has_value()) {
			countsByDialogIds[filter.dialogId.value()].filters++;
		}
	}
	for (const auto &exclusion : exclusions) {
		countsByDialogIds[exclusion.dialogId].exclusions++;
	}

	for (const auto &[id, count] : countsByDialogIds) {
		PeerId peerId = PeerId(PeerIdHelper(abs(id)));

		auto row = std::make_unique<PerDialogFiltersListRow>(peerId);
		auto status = QString();
		if (count.filters > 0) {
			status += tr::ayu_RegexFiltersAmount(tr::now, lt_count, count.filters);
			if (count.exclusions > 0) {
				status += ", ";
			}
		}
		if (count.exclusions > 0) {
			status += tr::ayu_RegexFiltersExcludedAmount(tr::now, lt_count, count.exclusions);
		}

		row->setCustomStatus(status, false);

		delegate()->peerListAppendRow(reinterpret_cast<std::unique_ptr<PeerListRow>&&>(row));
	}

	// sortByName();

	delegate()->peerListRefreshRows();
}

void PerDialogFiltersListController::rowClicked(not_null<PeerListRow*> peer) {
	ID did;
	if (peer->special()) {
		const ID pred = peer->id() & PeerId::kChatTypeMask;
		if (countsByDialogIds.contains(pred)) {
			did = pred;
		} else {
			did = -pred;
		}
	} else {
		did = getDialogIdFromPeer(peer->peer());
	}
	if (shadowBan) {
		auto _contextMenu = new Ui::PopupMenu(nullptr, st::popupMenuWithIcons);
		_contextMenu->setAttribute(Qt::WA_DeleteOnClose);

		_contextMenu->addAction(
			tr::lng_theme_delete(tr::now),
			[=]
			{
				if (ShadowBanUtils::isShadowBanned(did)) {
					ShadowBanUtils::removeShadowBan(did);
				} else {
					ShadowBanUtils::addShadowBan(did);
				}
			},
			&st::menuIconDelete);

		_contextMenu->popup(QCursor::pos());
		return;
	}
	_controller->dialogId = did;
	_controller->showExclude = true;
	_controller->showSettings(AyuFiltersList::Id());
}

}
