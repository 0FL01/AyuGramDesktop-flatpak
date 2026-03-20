// This is the source code of AyuGram for Desktop.
//
// We do not and cannot prevent the use of our code,
// but be respectful and credit the original author.
//
// Copyright @Radolyn, 2025
#include "ayu_logo.h"

#include <QSvgRenderer>

#include "ayu/ayu_settings.h"
#include "styles/style_ayu_styles.h"
#include "ui/rect.h"

static QString LAST_LOADED_NAME;
static QImage LAST_LOADED;
static QImage LAST_LOADED_PAD;

namespace AyuAssets {

void loadAppIco() {
	const auto &settings = AyuSettings::getInstance();

	QString appDataPath = QDir::fromNativeSeparators(qgetenv("APPDATA"));
	QString tempIconPath = appDataPath + "/AyuGram.ico";

	// workaround for read-only file
	auto f = QFile(tempIconPath);
	if (f.exists()) {
		f.setPermissions(QFile::WriteOther);
		f.remove();
	}
	f.close();
	QFile::copy(qsl(":/gui/art/ayu/%1/app_icon.ico").arg(settings.appIcon), tempIconPath);
}

QImage CreateImage(const QString &name, const QSize resultImageSize, const int padding = 0) {
	const auto iconSize = resultImageSize.shrunkBy(QMargins(padding, padding, padding, padding));

	const auto pngPath = qsl(":/gui/art/ayu/%1/app.png").arg(name);
	if (QFile::exists(pngPath)) {
		const auto loaded = QImage(pngPath).scaled(iconSize, Qt::KeepAspectRatio, Qt::SmoothTransformation);
		auto res = QImage(
			resultImageSize * style::DevicePixelRatio(),
			QImage::Format_ARGB32_Premultiplied);
		res.setDevicePixelRatio(style::DevicePixelRatio());
		res.fill(Qt::transparent);
		{
			auto p = QPainter(&res);
			p.drawImage(QRect(padding, padding, iconSize.width(), iconSize.height()), loaded);
		}
		return res;
	}

	const auto svgPath = qsl(":/gui/art/ayu/%1/app.svg").arg(name);
	if (!QFile::exists(svgPath)) {
		return {};
	}

	auto svg = QSvgRenderer(svgPath);
	auto image = QImage(
		resultImageSize * style::DevicePixelRatio(),
		QImage::Format_ARGB32_Premultiplied);
	image.setDevicePixelRatio(style::DevicePixelRatio());
	image.fill(Qt::transparent);
	{
		auto p = QPainter(&image);

		QPainterPath path;
		path.addRoundedRect(
			QRect(padding, padding, iconSize.width(), iconSize.height()),
			iconSize.width() / 2.0f,
			iconSize.height() / 2.0f
		);

		p.save();

		p.setRenderHint(QPainter::Antialiasing, true);
		p.setClipPath(path);
		p.setRenderHint(QPainter::Antialiasing, false);

		svg.render(&p, QRect(padding, padding, iconSize.width(), iconSize.height()));

		p.restore();
	}
	return image;
}

void loadIcons() {
	const auto &settings = AyuSettings::getInstance();
	if (LAST_LOADED_NAME != settings.appIcon) {
		LAST_LOADED_NAME = settings.appIcon;
		LAST_LOADED = CreateImage(settings.appIcon, Size(256));
		LAST_LOADED_PAD = CreateImage(settings.appIcon, Size(256), 12);
	}
}

QImage loadPreview(const QString &name) {
	return CreateImage(name, Size(st::cpIconSize), st::cpImagePadding);
}

QString currentAppLogoName() {
	return LAST_LOADED_NAME;
}

QImage currentAppLogo() {
	loadIcons();
	return LAST_LOADED;
}

QImage currentAppLogoPad() {
	loadIcons();
	return LAST_LOADED_PAD;
}

}
